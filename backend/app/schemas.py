"""Pydantic models for request and response payloads.

Define shapes of data that your API sends and receives here (e.g. Budget,
Transaction, Goal), separate from the SQLAlchemy models in `db/models.py`.
"""

from pydantic import BaseModel, field_serializer
from datetime import date, datetime
from typing import Optional
from decimal import Decimal


# naming these as items because they are used in lists
class TransactionItem(BaseModel):
    """Schema for transaction data sent to frontend."""
    id: int
    description: str
    amount: Decimal
    date: date  
    type: str
    
    @field_serializer('amount')
    def serialize_amount(self, value: Decimal) -> str:
        """Serialize Decimal to string to preserve precision."""
        return str(value)

class SpendingBreakdownItem(BaseModel):
    """Schema for spending breakdown data sent to frontend."""
    category: str
    amount: Decimal
    percentage: float
    
    @field_serializer('amount')
    def serialize_amount(self, value: Decimal) -> str:
        """Serialize Decimal to string to preserve precision."""
        return str(value)

class DashboardResponse(BaseModel):
    """Schema for dashboard data sent to frontend."""
    income: Decimal
    expenses: Decimal
    savings: Decimal
    assets: Decimal
    net_worth: Decimal
    spending_breakdown: list[SpendingBreakdownItem]
    recent_transactions: list[TransactionItem]
    
    @field_serializer('income', 'expenses', 'savings', 'assets', 'net_worth')
    def serialize_money(self, value: Decimal) -> str:
        """Serialize Decimal to string to preserve precision."""
        return str(value)


# Plaid schemas
class PublicTokenRequest(BaseModel):
    """Schema for Plaid public token exchange request."""
    public_token: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None

class AccountData(BaseModel):
    """Schema for account data."""
    plaid_account_id: str
    name: str
    account_type: str
    provider: str
    account_num: str
    balance: Decimal
    is_active: bool
    
    @field_serializer('balance')
    def serialize_balance(self, value: Decimal) -> str:
        """Serialize Decimal to string to preserve precision."""
        return str(value)


# Category schemas
class CategoryResponse(BaseModel):
    """Schema for category data."""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    icon: Optional[str]
    color: Optional[str]


# Account schemas
class AccountResponse(BaseModel):
    """Schema for account data."""
    model_config = {"from_attributes": True}
    
    id: int
    user_id: int
    name: str
    account_type: str
    provider: str
    balance: Decimal
    is_active: bool
    
    @field_serializer('balance')
    def serialize_balance(self, value: Decimal) -> str:
        """Serialize Decimal to string to preserve precision."""
        return str(value)


# Transaction schemas
class CategoryInTransaction(BaseModel):
    """Nested category in transaction response."""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    icon: Optional[str]
    color: Optional[str]


class AccountInTransaction(BaseModel):
    """Nested account in transaction response."""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    account_type: str


class TransactionDetailResponse(BaseModel):
    """Full transaction details."""
    model_config = {"from_attributes": True}
    
    id: int
    user_id: int
    account_id: int
    category_id: Optional[int]
    amount: Decimal
    date: date
    description: str
    normalized_merchant: Optional[str]
    is_subscription: bool
    tags: Optional[list[str]]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryInTransaction]
    account: AccountInTransaction
    
    @field_serializer('amount')
    def serialize_amount(self, value: Decimal) -> str:
        """Serialize Decimal to string to preserve precision."""
        return str(value)
    
    @field_serializer('date')
    def serialize_date(self, value: date) -> str:
        """Serialize date to ISO string."""
        return value.isoformat()
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO string."""
        return value.isoformat()


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""
    transactions: list[TransactionDetailResponse]
    total: int
    page: int
    pages: int


class TransactionCreateRequest(BaseModel):
    """Request to create a new transaction."""
    account_id: int
    amount: Decimal
    date: date
    description: str
    category_id: Optional[int] = None
    notes: Optional[str] = None


class TransactionUpdateRequest(BaseModel):
    """Request to update a transaction."""
    amount: Optional[Decimal] = None
    date: Optional[date] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    notes: Optional[str] = None


class UncategorizedCountResponse(BaseModel):
    """Count of uncategorized transactions."""
    count: int

