"""API routes for budget management.

Budgets are monthly spending targets per category.
Stats (spent, remaining, percent_used) are computed on-read from transactions.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date

from ..db.session import get_db
from ..db.models import Budget, Category, Transaction, User
from ..schemas import BudgetResponse, BudgetCreateRequest, BudgetUpdateRequest, CategoryResponse
from ..core.auth import get_current_user

router = APIRouter()


def compute_budget_stats_batch(
    db: Session,
    user_id: int,
    budgets: list[Budget]
) -> dict[int, dict[str, Decimal | float | bool]]:
    """Compute stats for multiple budgets efficiently (single query per period).
    
    Returns: {budget_id: {spent, remaining, percent_used, is_over_budget}}
    """
    if not budgets:
        return {}
    
    # Group budgets by (year, month) to minimize queries
    periods: dict[tuple[int, int], list[Budget]] = {}
    for budget in budgets:
        key = (budget.year, budget.month)
        if key not in periods:
            periods[key] = []
        periods[key].append(budget)
    
    # Compute stats for each period
    stats_by_budget_id: dict[int, dict[str, Decimal | float | bool]] = {}
    
    for (year, month), period_budgets in periods.items():
        # Calculate first and last day of month
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1)
        else:
            last_day = date(year, month + 1, 1)
        
        # Get all category IDs for this period
        category_ids = [b.category_id for b in period_budgets]
        
        # Single grouped query for this period
        query = (
            select(
                Transaction.category_id,
                func.coalesce(func.sum(-Transaction.amount), Decimal("0.00")).label("spent")
            )
            .where(
                Transaction.user_id == user_id,
                Transaction.category_id.in_(category_ids),
                Transaction.amount < 0,  # Expenses only
                Transaction.date >= first_day,
                Transaction.date < last_day
            )
            .group_by(Transaction.category_id)
        )
        
        results = db.execute(query).all()
        spent_by_category = {row.category_id: row.spent for row in results}
        
        # Calculate stats for each budget in this period
        for budget in period_budgets:
            spent = spent_by_category.get(budget.category_id, Decimal("0.00"))
            remaining = budget.amount - spent
            
            # Percent used (handle division by zero)
            if budget.amount > 0:
                percent_used = float((spent / budget.amount) * 100)
            else:
                percent_used = 0.0
            
            is_over_budget = spent > budget.amount
            
            stats_by_budget_id[budget.id] = {
                "spent": spent,
                "remaining": remaining,
                "percent_used": round(percent_used, 2),
                "is_over_budget": is_over_budget
            }
    
    return stats_by_budget_id


@router.get("/budgets", response_model=list[BudgetResponse])
def get_budgets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    month: int | None = None,
    year: int | None = None,
) -> list[BudgetResponse]:
    """Get all budgets for the current user, optionally filtered by month/year.
    
    Query params:
    - month: Filter by month (1-12)
    - year: Filter by year (e.g., 2026)
    """
    query = (
        select(Budget)
        .where(Budget.user_id == current_user.id)
        .options(joinedload(Budget.category))
        .order_by(Budget.year.desc(), Budget.month.desc(), Budget.category_id)
    )
    
    if month is not None:
        query = query.where(Budget.month == month)
    if year is not None:
        query = query.where(Budget.year == year)
    
    budgets = db.execute(query).unique().scalars().all()
    
    # Compute stats in batch
    stats = compute_budget_stats_batch(db, current_user.id, list(budgets))
    
    # Build responses
    responses = []
    for budget in budgets:
        budget_stats = stats.get(budget.id, {
            "spent": Decimal("0.00"),
            "remaining": budget.amount,
            "percent_used": 0.0,
            "is_over_budget": False
        })
        
        # Build response dict manually (computed fields don't exist on model)
        category_dict = CategoryResponse.model_validate(budget.category, from_attributes=True).model_dump()
        response_dict = {
            "id": budget.id,
            "user_id": budget.user_id,
            "category_id": budget.category_id,
            "month": budget.month,
            "year": budget.year,
            "amount": budget.amount,
            "created_at": budget.created_at,
            "updated_at": budget.updated_at,
            "category": category_dict,
            **budget_stats
        }
        response = BudgetResponse(**response_dict)
        responses.append(response)
    
    return responses


@router.get("/budgets/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BudgetResponse:
    """Get a single budget by ID."""
    query = (
        select(Budget)
        .where(Budget.id == budget_id, Budget.user_id == current_user.id)
        .options(joinedload(Budget.category))
    )
    
    budget = db.execute(query).unique().scalar_one_or_none()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Compute stats
    stats = compute_budget_stats_batch(db, current_user.id, [budget])
    budget_stats = stats.get(budget.id, {
        "spent": Decimal("0.00"),
        "remaining": budget.amount,
        "percent_used": 0.0,
        "is_over_budget": False
    })
    
    # Build response dict manually (computed fields don't exist on model)
    category_dict = CategoryResponse.model_validate(budget.category, from_attributes=True).model_dump()
    response_dict = {
        "id": budget.id,
        "user_id": budget.user_id,
        "category_id": budget.category_id,
        "month": budget.month,
        "year": budget.year,
        "amount": budget.amount,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
        "category": category_dict,
        **budget_stats
    }
    return BudgetResponse(**response_dict)


@router.post("/budgets", response_model=BudgetResponse, status_code=201)
def create_budget(
    request: BudgetCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BudgetResponse:
    """Create a new budget."""
    # Validate amount
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Budget amount must be greater than 0")
    
    # Validate month
    if not (1 <= request.month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    # Validate category exists
    category = db.execute(
        select(Category).where(Category.id == request.category_id)
    ).scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check for duplicate (user, category, month, year)
    existing = db.execute(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.category_id == request.category_id,
            Budget.month == request.month,
            Budget.year == request.year
        )
    ).scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Budget already exists for {category.name} in {request.month}/{request.year}"
        )
    
    # Create budget
    budget = Budget(
        user_id=current_user.id,
        category_id=request.category_id,
        month=request.month,
        year=request.year,
        amount=request.amount
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    
    # Load relationship
    db.refresh(budget, ["category"])
    
    # Compute stats
    stats = compute_budget_stats_batch(db, current_user.id, [budget])
    budget_stats = stats.get(budget.id, {
        "spent": Decimal("0.00"),
        "remaining": budget.amount,
        "percent_used": 0.0,
        "is_over_budget": False
    })
    
    # Build response dict manually (computed fields don't exist on model)
    category_dict = CategoryResponse.model_validate(budget.category, from_attributes=True).model_dump()
    response_dict = {
        "id": budget.id,
        "user_id": budget.user_id,
        "category_id": budget.category_id,
        "month": budget.month,
        "year": budget.year,
        "amount": budget.amount,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
        "category": category_dict,
        **budget_stats
    }
    return BudgetResponse(**response_dict)


@router.put("/budgets/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    request: BudgetUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BudgetResponse:
    """Update a budget (only amount can be updated)."""
    query = (
        select(Budget)
        .where(Budget.id == budget_id, Budget.user_id == current_user.id)
        .options(joinedload(Budget.category))
    )
    
    budget = db.execute(query).unique().scalar_one_or_none()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Update amount if provided
    if request.amount is not None:
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Budget amount must be greater than 0")
        budget.amount = request.amount
    
    db.commit()
    db.refresh(budget)
    
    # Compute stats
    stats = compute_budget_stats_batch(db, current_user.id, [budget])
    budget_stats = stats.get(budget.id, {
        "spent": Decimal("0.00"),
        "remaining": budget.amount,
        "percent_used": 0.0,
        "is_over_budget": False
    })
    
    # Build response dict manually (computed fields don't exist on model)
    category_dict = CategoryResponse.model_validate(budget.category, from_attributes=True).model_dump()
    response_dict = {
        "id": budget.id,
        "user_id": budget.user_id,
        "category_id": budget.category_id,
        "month": budget.month,
        "year": budget.year,
        "amount": budget.amount,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
        "category": category_dict,
        **budget_stats
    }
    return BudgetResponse(**response_dict)


@router.delete("/budgets/{budget_id}", status_code=204)
def delete_budget(
    budget_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a budget."""
    budget = db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    ).scalar_one_or_none()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    db.delete(budget)
    db.commit()
