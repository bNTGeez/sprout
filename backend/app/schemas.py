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
    plaid_item_id: Optional[int]
    name: str
    account_type: str
    provider: str
    balance: Decimal
    is_active: bool
    
    @field_serializer('balance')
    def serialize_balance(self, value: Decimal) -> str:
        """Serialize Decimal to string to preserve precision."""
        return str(value)


# Budget schemas
class BudgetResponse(BaseModel):
    """Budget with computed stats."""
    model_config = {"from_attributes": True}
    
    id: int
    user_id: int
    category_id: int
    month: int
    year: int
    amount: Decimal
    created_at: datetime
    updated_at: datetime
    category: CategoryResponse
    # Computed fields
    spent: Decimal
    remaining: Decimal
    percent_used: float
    is_over_budget: bool
    
    @field_serializer('amount', 'spent', 'remaining')
    def serialize_money(self, value: Decimal) -> str:
        """Serialize Decimal to string to preserve precision."""
        return str(value)
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO string."""
        return value.isoformat()


class BudgetCreateRequest(BaseModel):
    """Request to create a new budget."""
    category_id: int
    month: int
    year: int
    amount: Decimal


class BudgetUpdateRequest(BaseModel):
    """Request to update a budget."""
    amount: Optional[Decimal] = None


# Goal schemas
class GoalResponse(BaseModel):
    """Goal with computed progress."""
    model_config = {"from_attributes": True}
    
    id: int
    user_id: int
    name: str
    target_amount: Decimal
    current_amount: Decimal
    target_date: Optional[date]
    monthly_contribution: Optional[Decimal]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Computed fields
    progress_percent: float
    remaining: Decimal
    on_track: Optional[bool]
    is_met: bool
    
    @field_serializer('target_amount', 'current_amount', 'remaining')
    def serialize_money(self, value: Decimal) -> str:
        """Serialize Decimal to string to preserve precision."""
        return str(value)
    
    @field_serializer('monthly_contribution')
    def serialize_optional_money(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize optional Decimal to string or None."""
        return str(value) if value is not None else None
    
    @field_serializer('target_date')
    def serialize_optional_date(self, value: Optional[date]) -> Optional[str]:
        """Serialize optional date to ISO string or None."""
        return value.isoformat() if value is not None else None
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO string."""
        return value.isoformat()


class GoalCreateRequest(BaseModel):
    """Request to create a new goal."""
    name: str
    target_amount: Decimal
    target_date: Optional[date] = None
    monthly_contribution: Optional[Decimal] = None


class GoalUpdateRequest(BaseModel):
    """Request to update a goal."""
    name: Optional[str] = None
    target_amount: Optional[Decimal] = None
    target_date: Optional[date] = None
    monthly_contribution: Optional[Decimal] = None
    is_active: Optional[bool] = None


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


class GoalInTransaction(BaseModel):
    """Nested goal in transaction response (minimal for badges)."""
    model_config = {"from_attributes": True}
    
    id: int
    name: str


class TransactionDetailResponse(BaseModel):
    """Full transaction details."""
    model_config = {"from_attributes": True}
    
    id: int
    user_id: int
    account_id: int
    category_id: Optional[int]
    goal_id: Optional[int]
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
    goal: Optional[GoalInTransaction]
    
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
    goal_id: Optional[int] = None
    notes: Optional[str] = None
    normalized_merchant: Optional[str] = None


class TransactionUpdateRequest(BaseModel):
    """Request to update a transaction."""
    amount: Optional[Decimal] = None
    date: Optional[date] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    goal_id: Optional[int] = None
    notes: Optional[str] = None
    normalized_merchant: Optional[str] = None


class UncategorizedCountResponse(BaseModel):
    """Count of uncategorized transactions."""
    count: int


class TransactionStatsResponse(BaseModel):
    """Aggregated stats for a filtered transaction set."""
    total: int
    income: Decimal
    expenses: Decimal

    @field_serializer("income", "expenses")
    def serialize_decimal(self, value: Decimal) -> str:
        return str(value)

