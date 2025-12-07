"""Top-level API routes for the backend service.

Start by putting simple endpoints here (like `/health`), and later you can
split things into feature-specific route modules and include them in `main.py`.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date
from ..schemas import DashboardResponse, SpendingBreakdownItem, TransactionItem
from ..db.session import get_db
from ..db.models import User, Transaction, Account, Category, Holding

router = APIRouter()


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    """Get the dashboard data."""
    query = select(User)
    current_user = db.execute(query).scalar_one_or_none()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    today = date.today()
    current_month = today.month
    current_year = today.year
    
    # Calculate income (sum of positive transactions for current month)
    queryIncome = select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00"))).where(
        Transaction.user_id == current_user.id,
        Transaction.amount > 0,
        func.extract('month', Transaction.date) == current_month,
        func.extract('year', Transaction.date) == current_year,
    )
    income = float(db.execute(queryIncome).scalar_one())

    # Calculate expenses (sum of negative transactions for current month)
    queryExpenses = select(func.coalesce(func.sum(func.abs(Transaction.amount)), Decimal("0.00"))).where(
        Transaction.user_id == current_user.id,
        Transaction.amount < 0,
        func.extract('month', Transaction.date) == current_month,
        func.extract('year', Transaction.date) == current_year,
    )
    expenses = float(db.execute(queryExpenses).scalar_one())
    
    savings = income - expenses
    
    # Calculate assets (checking + savings + brokerage accounts + holdings)
    queryAccountAssets = select(func.coalesce(func.sum(Account.balance), Decimal("0.00"))).where(
        Account.user_id == current_user.id,
        Account.is_active == True,
        Account.account_type.in_(["checking", "savings", "brokerage"]),
    )
    account_balances = float(db.execute(queryAccountAssets).scalar_one())
    
    # Add holdings (investments)
    queryHoldings = select(func.coalesce(func.sum(Holding.total_value), Decimal("0.00"))).where(
        Holding.user_id == current_user.id
    )
    holdings_value = float(db.execute(queryHoldings).scalar_one())
    
    assets = account_balances + holdings_value
    
    # Calculate liabilities (credit card debt)
    queryLiabilities = select(func.coalesce(func.sum(func.abs(Account.balance)), Decimal("0.00"))).where(
        Account.user_id == current_user.id,
        Account.is_active == True,
        Account.account_type == "credit_card",
        Account.balance < 0,  # Only negative balances are debt
    )
    liabilities = float(db.execute(queryLiabilities).scalar_one())
    
    # Net worth = assets - liabilities
    net_worth = assets - liabilities

    querySpendingBreakdown = select(
        Category.name,  
        func.sum(func.abs(Transaction.amount)).label('total')  
    )

    querySpendingBreakdown = querySpendingBreakdown.join(
        Transaction,  
        Transaction.category_id == Category.id  
    )
    
    querySpendingBreakdown = querySpendingBreakdown.where(
        Transaction.user_id == current_user.id,  
        Transaction.amount < 0,
        func.extract('month', Transaction.date) == current_month,
        func.extract('year', Transaction.date) == current_year,
    )

    querySpendingBreakdown = querySpendingBreakdown.group_by(Category.name)

    spending_query = db.execute(querySpendingBreakdown).all()

    total_spending = sum(float(row.total) for row in spending_query) if spending_query else 0.0

    spending_breakdown = [
        SpendingBreakdownItem(
            category=row.name,  
            amount=float(row.total), 
            percentage=round((float(row.total) / total_spending) * 100, 1) if total_spending > 0 else 0.0
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
            amount=float(tx.amount),
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
