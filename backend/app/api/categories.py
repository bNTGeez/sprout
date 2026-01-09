"""API routes for category management."""

from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db.session import get_db
from ..db.models import Category
from ..schemas import CategoryResponse

router = APIRouter()


@router.get("/categories", response_model=list[CategoryResponse])
def get_categories(
    db: Annotated[Session, Depends(get_db)],
) -> list[CategoryResponse]:
    """Get all available categories.
    
    Categories are global (not user-specific) and are seeded in the database.
    """
    
    query = select(Category).order_by(Category.name)
    categories = db.execute(query).scalars().all()
    
    # Pydantic handles serialization with from_attributes=True
    return categories
