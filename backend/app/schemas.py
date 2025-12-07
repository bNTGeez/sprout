"""Pydantic models for request and response payloads.

Define shapes of data that your API sends and receives here (e.g. Budget,
Transaction, Goal), separate from the SQLAlchemy models in `db/models.py`.
"""

from pydantic import BaseModel
from datetime import date


# naming these as items because they are used in lists
class TransactionItem(BaseModel):
    """Schema for transaction data sent to frontend."""
    id: int
    description: str
    amount: float
    date: date  
    type: str

class SpendingBreakdownItem(BaseModel):
    """Schema for spending breakdown data sent to frontend."""
    category: str
    amount: float
    percentage: float

class DashboardResponse(BaseModel):
    """Schema for dashboard data sent to frontend."""
    income: float
    expenses: float
    savings: float
    assets: float
    net_worth: float  
    spending_breakdown: list[SpendingBreakdownItem]
    recent_transactions: list[TransactionItem]


# Plaid schemas
class PublicTokenRequest(BaseModel):
    """Schema for Plaid public token exchange request."""
    public_token: str
    institution_id: str | None = None
    institution_name: str | None = None

class AccountData(BaseModel):
    """Schema for account data."""
    plaid_account_id: str
    name: str
    account_type: str
    provider: str
    account_num: str
    balance: float
    is_active: bool

