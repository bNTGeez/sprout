"""API routes for transaction management."""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, or_
from datetime import date
from decimal import Decimal

from ..db.session import get_db
from ..db.models import User, Transaction, Category, Account, Goal
from ..core.auth import get_current_user
from ..schemas import (
    TransactionListResponse,
    TransactionDetailResponse,
    TransactionCreateRequest,
    TransactionUpdateRequest,
    UncategorizedCountResponse,
)

router = APIRouter()


def update_goal_amount(
    db: Session,
    goal_id: int | None,
    old_goal_id: int | None,
    new_amount: Decimal,
    old_amount: Decimal,
) -> None:
    """Update goal current_amount based on transaction changes.
    
    Per guide section 4: Goals are savings goals.
    Only positive amounts contribute: contrib(amount) = amount if amount > 0 else 0
    
    This handles:
    - Creating transaction with goal_id
    - Updating transaction amount
    - Moving transaction between goals
    - Removing goal from transaction
    - Deleting transaction
    - Sign flips (+ → - or - → +)
    """
    def contrib(amount: Decimal) -> Decimal:
        """Calculate contribution: only positive amounts contribute."""
        return amount if amount > 0 else Decimal("0.00")
    
    old_contrib = contrib(old_amount)
    new_contrib = contrib(new_amount)
    
    # Handle goal changes
    if old_goal_id != goal_id:
        # Goal changed - subtract from old, add to new
        if old_goal_id:
            # Subtract old contribution from old goal
            old_goal = db.execute(
                select(Goal).where(Goal.id == old_goal_id).with_for_update()
            ).scalar_one_or_none()
            if old_goal:
                old_goal.current_amount -= old_contrib
        
        if goal_id:
            # Add new contribution to new goal
            new_goal = db.execute(
                select(Goal).where(Goal.id == goal_id).with_for_update()
            ).scalar_one_or_none()
            if new_goal:
                new_goal.current_amount += new_contrib
    else:
        # Same goal - apply delta
        if goal_id:
            goal = db.execute(
                select(Goal).where(Goal.id == goal_id).with_for_update()
            ).scalar_one_or_none()
            if goal:
                delta = new_contrib - old_contrib
                goal.current_amount += delta


@router.get("/transactions", response_model=TransactionListResponse)
def get_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    is_uncategorized: Optional[bool] = None,
) -> TransactionListResponse:
    """Get paginated list of transactions with optional filters."""
    
    # Build base filter query (no joins, no ordering - just for counting)
    base_filters = [Transaction.user_id == current_user.id]
    
    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        base_filters.append(
            or_(
                Transaction.description.ilike(search_pattern),
                func.coalesce(Transaction.normalized_merchant, "").ilike(search_pattern)
            )
        )
    
    if category_id is not None:
        base_filters.append(Transaction.category_id == category_id)
    
    if date_from:
        base_filters.append(Transaction.date >= date_from)
    
    if date_to:
        base_filters.append(Transaction.date <= date_to)
    
    if min_amount is not None:
        base_filters.append(Transaction.amount >= min_amount)
    
    if max_amount is not None:
        base_filters.append(Transaction.amount <= max_amount)
    
    if is_uncategorized is not None:
        if is_uncategorized:
            base_filters.append(Transaction.category_id.is_(None))
        else:
            base_filters.append(Transaction.category_id.isnot(None))
    
    # Get total count (efficient - no joins, no ordering)
    count_query = select(func.count(Transaction.id)).where(*base_filters)
    total = db.execute(count_query).scalar_one()
    
    # Calculate pagination
    pages = max(1, (total + limit - 1) // limit)  # At least 1 page, even if empty
    offset = (page - 1) * limit
    
    # Build data query with joins and ordering
    data_query = (
        select(Transaction)
        .options(
            joinedload(Transaction.category),
            joinedload(Transaction.account),
            joinedload(Transaction.goal)
        )
        .where(*base_filters)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset(offset)
        .limit(limit)
    )
    
    # Execute data query
    transactions = db.execute(data_query).unique().scalars().all()
    
    # Pydantic will handle serialization with from_attributes=True
    return TransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        pages=pages,
    )


@router.get("/transactions/uncategorized/count", response_model=UncategorizedCountResponse)
def get_uncategorized_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UncategorizedCountResponse:
    """Get count of uncategorized transactions."""
    
    count = db.execute(
        select(func.count(Transaction.id))
        .where(
            Transaction.user_id == current_user.id,
            Transaction.category_id.is_(None)
        )
    ).scalar_one()
    
    return UncategorizedCountResponse(count=count)


@router.get("/transactions/{transaction_id}", response_model=TransactionDetailResponse)
def get_transaction(
    transaction_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TransactionDetailResponse:
    """Get a single transaction by ID."""
    
    query = (
        select(Transaction)
        .options(
            joinedload(Transaction.category),
            joinedload(Transaction.account),
            joinedload(Transaction.goal)
        )
        .where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    )
    
    tx = db.execute(query).unique().scalar_one_or_none()
    
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return tx  # Pydantic handles serialization


@router.post("/transactions", response_model=TransactionDetailResponse, status_code=201)
def create_transaction(
    request: TransactionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TransactionDetailResponse:
    """Create a new manual transaction."""
    
    # Verify account belongs to user
    account = db.execute(
        select(Account).where(
            Account.id == request.account_id,
            Account.user_id == current_user.id
        )
    ).scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=400, detail="Invalid account_id")
    
    # Verify category exists if provided
    if request.category_id is not None:
        category = db.execute(
            select(Category).where(Category.id == request.category_id)
        ).scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category_id")
    
    # Verify goal belongs to user if provided
    if request.goal_id is not None:
        goal = db.execute(
            select(Goal).where(
                Goal.id == request.goal_id,
                Goal.user_id == current_user.id
            )
        ).scalar_one_or_none()
        
        if not goal:
            raise HTTPException(status_code=400, detail="Invalid goal_id or goal does not belong to user")
    
    # Create transaction
    transaction = Transaction(
        user_id=current_user.id,
        account_id=request.account_id,
        category_id=request.category_id,
        goal_id=request.goal_id,
        amount=request.amount,
        date=request.date,
        description=request.description,
        notes=request.notes,
        normalized_merchant=request.normalized_merchant,
        is_subscription=False,
    )
    
    db.add(transaction)
    db.flush()  # Get transaction.id before updating goal
    
    # Auto-sync goal amount
    if request.goal_id:
        update_goal_amount(
            db=db,
            goal_id=request.goal_id,
            old_goal_id=None,
            new_amount=request.amount,
            old_amount=Decimal("0.00")
        )
    
    db.commit()
    
    # Reload with relationships for response
    tx = db.execute(
        select(Transaction)
        .options(
            joinedload(Transaction.category),
            joinedload(Transaction.account),
            joinedload(Transaction.goal)
        )
        .where(Transaction.id == transaction.id)
    ).unique().scalar_one()
    
    return tx  # Pydantic handles serialization


@router.put("/transactions/{transaction_id}", response_model=TransactionDetailResponse)
def update_transaction(
    transaction_id: int,
    request: TransactionUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TransactionDetailResponse:
    """Update an existing transaction."""
    
    # Get transaction
    transaction = db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    ).scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get fields that were explicitly set (to distinguish None from unset)
    update_data = request.model_dump(exclude_unset=True)
    
    # Verify category if provided and not None
    if "category_id" in update_data and update_data["category_id"] is not None:
        category = db.execute(
            select(Category).where(Category.id == update_data["category_id"])
        ).scalar_one_or_none()
        
        if not category:
            raise HTTPException(status_code=400, detail="Invalid category_id")
    
    # Verify goal belongs to user if provided and not None
    if "goal_id" in update_data and update_data["goal_id"] is not None:
        goal = db.execute(
            select(Goal).where(
                Goal.id == update_data["goal_id"],
                Goal.user_id == current_user.id
            )
        ).scalar_one_or_none()
        
        if not goal:
            raise HTTPException(status_code=400, detail="Invalid goal_id or goal does not belong to user")
    
    # Track old values for goal auto-sync
    old_amount = transaction.amount
    old_goal_id = transaction.goal_id
    
    # Update fields that were explicitly provided
    if "amount" in update_data:
        transaction.amount = update_data["amount"]  # Already Decimal from schema
    
    if "date" in update_data:
        transaction.date = update_data["date"]
    
    if "description" in update_data:
        transaction.description = update_data["description"]
    
    if "category_id" in update_data:
        transaction.category_id = update_data["category_id"]  # Can be None to clear
    
    if "goal_id" in update_data:
        transaction.goal_id = update_data["goal_id"]  # Can be None to clear
    
    if "notes" in update_data:
        transaction.notes = update_data["notes"]
    
    if "normalized_merchant" in update_data:
        transaction.normalized_merchant = update_data["normalized_merchant"]
    
    # Auto-sync goal amount if amount or goal_id changed
    if "amount" in update_data or "goal_id" in update_data:
        update_goal_amount(
            db=db,
            goal_id=transaction.goal_id,
            old_goal_id=old_goal_id,
            new_amount=transaction.amount,
            old_amount=old_amount
        )
    
    db.commit()
    
    # Reload with relationships for response
    tx = db.execute(
        select(Transaction)
        .options(
            joinedload(Transaction.category),
            joinedload(Transaction.account),
            joinedload(Transaction.goal)
        )
        .where(Transaction.id == transaction.id)
    ).unique().scalar_one()
    
    return tx  # Pydantic handles serialization


@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Delete a transaction."""
    
    transaction = db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    ).scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Auto-sync goal amount (subtract contribution before deleting)
    if transaction.goal_id:
        update_goal_amount(
            db=db,
            goal_id=None,  # Removing from goal
            old_goal_id=transaction.goal_id,
            new_amount=Decimal("0.00"),
            old_amount=transaction.amount
        )
    
    db.delete(transaction)
    db.commit()
    
    return {"message": "Transaction deleted successfully"}
