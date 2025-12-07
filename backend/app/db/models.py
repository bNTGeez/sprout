"""SQLAlchemy ORM models for the backend.

These map your core financial concepts (users, accounts, transactions, goals,
budgets, holdings, insights, plans, Plaid items) to database tables.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Date, ForeignKey, String, Text, JSON, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

__all__ = ["Base", "User", "Account", "Transaction", "Category", "Budget", "Goal", "Holding", "Insight", "Plan", "PlaidItem"]


class User(Base):
    """Application user.

    Every other table references `user_id` so data stays scoped per user.
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[str]
    password_hash: Mapped[str]
    accounts: Mapped[list["Account"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[list["Goal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    holdings: Mapped[list["Holding"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    insights: Mapped[list["Insight"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    plans: Mapped[list["Plan"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    plaid_items: Mapped[list["PlaidItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Account(Base):
    """Financial account (checking, savings, credit card, brokerage, etc.).

    Ingestion Agent normalizes external data (Plaid, CSV, manual) into these.
    """
    __tablename__ = "accounts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    plaid_item_id: Mapped[int | None] = mapped_column(ForeignKey("plaid_items.id"), nullable=True)
    plaid_account_id: Mapped[str | None] = mapped_column(nullable=True)
    name: Mapped[str]
    account_type: Mapped[str] 
    provider: Mapped[str]
    account_num: Mapped[str]
    balance: Mapped[Decimal] = mapped_column(Numeric(15, 2))  # Up to $9,999,999,999,999.99
    is_active: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="accounts")
    plaid_item: Mapped["PlaidItem | None"] = relationship(back_populates="accounts")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account")
    holdings: Mapped[list["Holding"]] = relationship(back_populates="account")


class Category(Base):
    """Spending category (e.g. Dining, Shopping, Subscriptions)."""
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    icon: Mapped[str | None] = mapped_column(nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)  # Hex color like "#FF5733"
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="category")
    insights: Mapped[list["Insight"]] = relationship(back_populates="related_category")


class Transaction(Base):
    """Single financial event (income or expense)."""
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))  # Exact decimal for money
    date: Mapped[datetime] = mapped_column(Date)  # Only date, no time
    description: Mapped[str]
    normalized_merchant: Mapped[str | None] = mapped_column(nullable=True)  # Nullable until Classification Agent processes
    provider_tx_id: Mapped[str | None] = mapped_column(nullable=True, unique=True, index=True)  # For deduplication
    plaid_transaction_id: Mapped[str | None] = mapped_column(nullable=True, unique=True, index=True)  
    is_subscription: Mapped[bool] = mapped_column(default=False)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # JSON array
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="transactions")
    account: Mapped["Account"] = relationship(back_populates="transactions")
    category: Mapped["Category | None"] = relationship(back_populates="transactions")
    insights: Mapped[list["Insight"]] = relationship(back_populates="related_transaction")


class Budget(Base):
    """Monthly budget target for a (user, category)."""
    __tablename__ = "budgets"
    __table_args__ = (
        # A user can only have ONE budget per category per month/year
        UniqueConstraint("user_id", "category_id", "month", "year", name="uq_user_category_period"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))  # Target budget amount
    month: Mapped[int]  # 1-12
    year: Mapped[int]
    is_auto_generated: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="budgets")
    category: Mapped["Category"] = relationship(back_populates="budgets")


class Goal(Base):
    """Savings goal (e.g. Emergency Fund, Vacation)."""
    __tablename__ = "goals"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str]
    target_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    current_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"))
    target_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)  # Optional deadline
    monthly_contribution: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)  # Recommended by agent
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="goals")


class Holding(Base):
    """Investment position (stock, ETF, crypto, etc.)."""
    __tablename__ = "holdings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    symbol: Mapped[str]
    name: Mapped[str]
    asset_type: Mapped[str]
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))  # Supports crypto with 8 decimals
    current_price: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    total_value: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    last_updated: Mapped[datetime]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="holdings")
    account: Mapped["Account"] = relationship(back_populates="holdings")


class Insight(Base):
    """AI-generated pattern / warning, plus the raw data behind it."""
    __tablename__ = "insights"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    insight_type: Mapped[str]
    title: Mapped[str]
    description: Mapped[str]
    raw_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # JSON data
    severity: Mapped[str]  # "info", "warning", "alert"
    related_category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    related_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="insights")
    related_category: Mapped["Category | None"] = relationship(back_populates="insights")
    related_transaction: Mapped["Transaction | None"] = relationship(back_populates="insights")


class Plan(Base):
    """AI-generated monthly financial plan for a user."""
    __tablename__ = "plans"
    __table_args__ = (
        # Only one plan per user per month/year
        UniqueConstraint("user_id", "month", "year", name="uq_user_plan_period"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    month: Mapped[int]  # 1-12
    year: Mapped[int]
    summary_text: Mapped[str] = mapped_column(Text)
    recommended_budgets: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    recommended_goal_contributions: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    action_items: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="plans")


class PlaidItem(Base):
    """Plaid connection (one per institution link).

    One PlaidItem can back multiple `Account` rows for the same bank.
    """
    __tablename__ = "plaid_items"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    plaid_item_id: Mapped[str] = mapped_column(unique=True, index=True)
    access_token: Mapped[str]  # Encrypted Plaid access token 
    institution_id: Mapped[str]
    institution_name: Mapped[str]
    status: Mapped[str] = mapped_column(default="good")  # "good", "error", "requires_reauth"
    error_code: Mapped[str | None] = mapped_column(nullable=True)
    last_successful_update: Mapped[datetime | None] = mapped_column(nullable=True)
    last_webhook_update: Mapped[datetime | None] = mapped_column(nullable=True)
    transactions_cursor: Mapped[str | None] = mapped_column(nullable=True)  # For incremental transaction syncs
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="plaid_items")
    accounts: Mapped[list["Account"]] = relationship(back_populates="plaid_item")
    


