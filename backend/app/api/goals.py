"""API routes for goal management.

Goals are savings targets that track progress toward a financial objective.
Progress is computed from goal.current_amount (which is auto-synced from transactions).
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal
from datetime import date

from ..db.session import get_db
from ..db.models import Goal, User
from ..schemas import GoalResponse, GoalCreateRequest, GoalUpdateRequest
from ..core.auth import get_current_user

router = APIRouter()


def compute_goal_progress(goal: Goal) -> dict[str, Decimal | float | bool | None]:
    """Compute progress stats for a single goal.
    
    Returns: {progress_percent, remaining, on_track}
    """
    # Progress percent
    if goal.target_amount > 0:
        progress_percent = float((goal.current_amount / goal.target_amount) * 100)
    else:
        progress_percent = 0.0
    
    # Remaining
    remaining = goal.target_amount - goal.current_amount
    
    # Is goal met?
    is_met = goal.current_amount >= goal.target_amount
    
    # On track (only if target_date and monthly_contribution exist, and goal not yet met)
    on_track = None
    if not is_met and goal.target_date and goal.monthly_contribution:
        # Goal not yet met - calculate if on track
        today = date.today()
        
        if goal.target_date <= today:
            # Target date is past and goal not met - behind
            on_track = False
        else:
            # Calculate months remaining
            days_remaining = (goal.target_date - today).days
            months_remaining = max(1, days_remaining / 30.44)  # Average days per month
            
            # Calculate required monthly contribution
            if months_remaining > 0:
                required_monthly = remaining / Decimal(str(months_remaining))
                on_track = goal.monthly_contribution >= required_monthly
            else:
                # No time left - check if goal is met
                on_track = goal.current_amount >= goal.target_amount
    
    return {
        "progress_percent": round(progress_percent, 2),
        "remaining": remaining,
        "on_track": on_track,
        "is_met": is_met
    }


@router.get("/goals", response_model=list[GoalResponse])
def get_goals(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    is_active: bool | None = None,
) -> list[GoalResponse]:
    """Get all goals for the current user.
    
    Query params:
    - is_active: Filter by active status (true/false)
    """
    query = select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.created_at.desc())
    
    if is_active is not None:
        query = query.where(Goal.is_active == is_active)
    
    goals = db.execute(query).scalars().all()
    
    # Build responses
    responses = []
    for goal in goals:
        progress_stats = compute_goal_progress(goal)
        
        response_dict = {
            "id": goal.id,
            "user_id": goal.user_id,
            "name": goal.name,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "target_date": goal.target_date,
            "monthly_contribution": goal.monthly_contribution,
            "is_active": goal.is_active,
            "created_at": goal.created_at,
            "updated_at": goal.updated_at,
            **progress_stats
        }
        response = GoalResponse(**response_dict)
        responses.append(response)
    
    return responses


@router.get("/goals/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GoalResponse:
    """Get a single goal by ID."""
    goal = db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    ).scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Compute progress
    progress_stats = compute_goal_progress(goal)
    
    response_dict = {
        "id": goal.id,
        "user_id": goal.user_id,
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "target_date": goal.target_date,
        "monthly_contribution": goal.monthly_contribution,
        "is_active": goal.is_active,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        **progress_stats
    }
    return GoalResponse(**response_dict)


@router.post("/goals", response_model=GoalResponse, status_code=201)
def create_goal(
    request: GoalCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GoalResponse:
    """Create a new goal."""
    # Validate target_amount
    if request.target_amount <= 0:
        raise HTTPException(status_code=400, detail="Target amount must be greater than 0")
    
    # Validate monthly_contribution if provided
    if request.monthly_contribution is not None and request.monthly_contribution <= 0:
        raise HTTPException(status_code=400, detail="Monthly contribution must be greater than 0")
    
    # Create goal
    goal = Goal(
        user_id=current_user.id,
        name=request.name,
        target_amount=request.target_amount,
        current_amount=Decimal("0.00"),  # Always starts at 0
        target_date=request.target_date,
        monthly_contribution=request.monthly_contribution,
        is_active=True
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    # Compute progress
    progress_stats = compute_goal_progress(goal)
    
    response_dict = {
        "id": goal.id,
        "user_id": goal.user_id,
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "target_date": goal.target_date,
        "monthly_contribution": goal.monthly_contribution,
        "is_active": goal.is_active,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        **progress_stats
    }
    return GoalResponse(**response_dict)


@router.put("/goals/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    request: GoalUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GoalResponse:
    """Update a goal."""
    goal = db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    ).scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    # Update fields if provided
    if request.name is not None:
        goal.name = request.name
    
    if request.target_amount is not None:
        if request.target_amount <= 0:
            raise HTTPException(status_code=400, detail="Target amount must be greater than 0")
        goal.target_amount = request.target_amount
    
    if request.target_date is not None:
        goal.target_date = request.target_date
    
    if request.monthly_contribution is not None:
        if request.monthly_contribution <= 0:
            raise HTTPException(status_code=400, detail="Monthly contribution must be greater than 0")
        goal.monthly_contribution = request.monthly_contribution
    
    if request.is_active is not None:
        goal.is_active = request.is_active
    
    db.commit()
    db.refresh(goal)
    
    # Compute progress
    progress_stats = compute_goal_progress(goal)
    
    response_dict = {
        "id": goal.id,
        "user_id": goal.user_id,
        "name": goal.name,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "target_date": goal.target_date,
        "monthly_contribution": goal.monthly_contribution,
        "is_active": goal.is_active,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        **progress_stats
    }
    return GoalResponse(**response_dict)


@router.delete("/goals/{goal_id}", status_code=204)
def delete_goal(
    goal_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete a goal.
    
    Note: This will set goal_id to NULL for any linked transactions (ON DELETE SET NULL).
    """
    goal = db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    ).scalar_one_or_none()
    
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    db.delete(goal)
    db.commit()
