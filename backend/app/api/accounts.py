"""API routes for account management."""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db.session import get_db
from ..db.models import User, Account
from ..core.auth import get_current_user
from ..schemas import AccountResponse

router = APIRouter()


@router.get("/accounts", response_model=list[AccountResponse])
def get_accounts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AccountResponse]:
    """Get all accounts for the current user."""
    
    query = (
        select(Account)
        .where(Account.user_id == current_user.id)
        .order_by(Account.name)
    )
    
    accounts = db.execute(query).scalars().all()
    
    # Pydantic handles serialization with from_attributes=True
    return accounts
