
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWTError, InvalidTokenError
from sqlalchemy.orm import Session
from sqlalchemy import select

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
    
    # Find user by email since Supabase manages auth
    query = select(User).where(User.email == user_email)
    user = db.execute(query).scalar_one_or_none()
    
    # Auto-create user if doesn't exist 
    if not user:
        user = User(
            email=user_email,
            name=user_email.split("@")[0],  # Use email prefix as default name
            password_hash="supabase_managed"  # Placeholder since supabase handles auth
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user
