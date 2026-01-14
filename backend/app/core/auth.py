
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWTError, InvalidTokenError
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from ..core.config import get_settings
from ..db.session import get_db
from ..db.models import User

settings = get_settings()
security = HTTPBearer()


def verify_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> dict:
    """Verify Supabase JWT token and return decoded payload.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        Decoded JWT payload containing user info
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials
    
    secret = (settings.supabase_jwt_secret or "").strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SUPABASE_JWT_SECRET is not configured"
        )

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience="authenticated",
            options={"verify_exp": True},
        )
        
        return payload
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )


def get_current_user(
    token_payload: Annotated[dict, Depends(verify_token)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """Get current user from database based on Supabase token.
    
    Args:
        token_payload: Decoded JWT payload from verify_token
        db: Database session
        
    Returns:
        User model instance
        
    Raises:
        HTTPException: If user not found in database
    """

    supabase_user_id = token_payload.get("sub")
    user_email = token_payload.get("email")
    
    if not supabase_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID"
        )
    
    # Parse Supabase `sub` (UUID string) to a UUID object for Postgres uuid comparisons.
    supabase_user_uuid: uuid.UUID | None = None
    try:
        supabase_user_uuid = uuid.UUID(str(supabase_user_id))
    except Exception:
        supabase_user_uuid = None

    # Prefer matching by Supabase user id; fall back to email for legacy rows.
    conditions = [User.email == user_email]
    if supabase_user_uuid is not None:
        conditions.insert(0, User.auth_user_id == supabase_user_uuid)
    query = select(User).where(or_(*conditions))
    user = db.execute(query).scalar_one_or_none()

    # Backfill auth_user_id for users created before we stored it.
    if user and not user.auth_user_id and supabase_user_uuid is not None:
        user.auth_user_id = supabase_user_uuid
        db.commit()
        db.refresh(user)
    
    # Auto-create user if doesn't exist 
    if not user:
        from ..db.models import Account
        from decimal import Decimal
        
        user = User(
            email=user_email,
            name=user_email.split("@")[0],  # Use email prefix as default name
            password_hash="supabase_managed",  # Placeholder since supabase handles auth
            auth_user_id=supabase_user_uuid  # Store Supabase auth UUID
        )
        db.add(user)
        db.flush()  # Flush to get user.id
        
        # Create default accounts for new user
        default_accounts = [
            Account(
                user_id=user.id,
                name="Cash",
                account_type="cash",
                provider="manual",
                account_num=None,  # Manual accounts don't have account numbers
                balance=Decimal("0"),
                is_active=True,
            ),
            Account(
                user_id=user.id,
                name="Checking",
                account_type="depository",
                provider="manual",
                account_num=None,  # Manual accounts don't have account numbers
                balance=Decimal("0"),
                is_active=True,
            ),
        ]
        
        for account in default_accounts:
            db.add(account)
        
        db.commit()
        db.refresh(user)
    
    return user
