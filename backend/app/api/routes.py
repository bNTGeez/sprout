"""Top-level API routes for the backend service.

Start by putting simple endpoints here (like `/health`), and later you can
split things into feature-specific route modules and include them in `main.py`.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date
from ..schemas import DashboardResponse, SpendingBreakdownItem, TransactionItem
from ..db.session import get_db
from ..db.models import User, Transaction, Account, Category, Holding
from ..core.auth import get_current_user

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> DashboardResponse:
    """Get the dashboard data."""
    
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Calculate first and last day of current month (date range)
    first_day = date(current_year, current_month, 1)
    if current_month == 12:
        last_day = date(current_year + 1, 1, 1)
    else:
        last_day = date(current_year, current_month + 1, 1)
    
    # Calculate income (sum of positive transactions for current month)
    queryIncome = select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
        Transaction.user_id == current_user.id,
        Transaction.amount > 0,
        Transaction.date >= first_day,
        Transaction.date < last_day,
    )
    income = db.execute(queryIncome).scalar_one()

    # Calculate expenses (sum of negative transactions for current month)
    # Use -func.sum() instead of func.abs() per guide
    queryExpenses = select(func.coalesce(-func.sum(Transaction.amount), Decimal("0.00"))).where(
        Transaction.user_id == current_user.id,
        Transaction.amount < 0,
        Transaction.date >= first_day,
        Transaction.date < last_day,
    )
    expenses = db.execute(queryExpenses).scalar_one()
    
    savings = income - expenses
    
    # Calculate assets (checking + savings + brokerage accounts + holdings)
    queryAccountAssets = select(func.coalesce(func.sum(Account.balance), Decimal("0.00"))).where(
        Account.user_id == current_user.id,
        Account.is_active == True,
        Account.account_type.in_(["checking", "savings", "brokerage"]),
    )
    account_balances = db.execute(queryAccountAssets).scalar_one()
    
    # Add holdings (investments)
    queryHoldings = select(func.coalesce(func.sum(Holding.total_value), Decimal("0.00"))).where(
        Holding.user_id == current_user.id
    )
    holdings_value = db.execute(queryHoldings).scalar_one()
    
    assets = account_balances + holdings_value
    
    # Calculate liabilities (credit card debt)
    # Plaid returns credit card balances as positive (amount owed), so we sum them as-is
    # If balance is negative, it means credit (overpayment), so we use abs() to get the debt amount
    queryLiabilities = select(
        func.coalesce(
            func.sum(func.abs(Account.balance)), 
            Decimal("0.00")
        )
    ).where(
        Account.user_id == current_user.id,
        Account.is_active == True,
        Account.account_type == "credit_card",
    )
    liabilities = db.execute(queryLiabilities).scalar_one()
    
    # Net worth = assets - liabilities
    net_worth = assets - liabilities

    querySpendingBreakdown = select(
        Category.name,  
        func.sum(-Transaction.amount).label('total')  # Use -func.sum() instead of func.abs()
    )

    querySpendingBreakdown = querySpendingBreakdown.join(
        Transaction,  
        Transaction.category_id == Category.id  
    )
    
    querySpendingBreakdown = querySpendingBreakdown.where(
        Transaction.user_id == current_user.id,  
        Transaction.amount < 0,
        Transaction.date >= first_day,
        Transaction.date < last_day,
    )

    querySpendingBreakdown = querySpendingBreakdown.group_by(Category.name)

    spending_query = db.execute(querySpendingBreakdown).all()

    # Keep as Decimal for calculation, convert to float only for percentage
    total_spending = sum(row.total for row in spending_query) if spending_query else Decimal("0.00")

    spending_breakdown = [
        SpendingBreakdownItem(
            category=row.name,  
            amount=row.total,  # Keep as Decimal
            percentage=round(float((row.total / total_spending) * 100), 1) if total_spending > 0 else 0.0
        )
        for row in spending_query
    ]
    
    queryRecentTransactions = select(Transaction).where(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.date.desc()).limit(10)
    
    recent_txs = db.execute(queryRecentTransactions).scalars().all()
    
    recent_transactions = [
        TransactionItem(
            id=tx.id,
            description=tx.description,
            amount=tx.amount,  # Keep as Decimal
            date=tx.date,
            type="income" if tx.amount >= 0 else "expense"
        )
        for tx in recent_txs
    ]

    return DashboardResponse(
        income=income,
        expenses=expenses,
        savings=savings,
        assets=assets,
        net_worth=net_worth,
        spending_breakdown=spending_breakdown,
        recent_transactions=recent_transactions
    )
