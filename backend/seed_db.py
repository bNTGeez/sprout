"""Database seeding script.

Run this to populate your database with sample data for testing.
Usage: python seed_db.py
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from app.db.base import Base
from app.db.models import (
    User,
    Account,
    Category,
    Transaction,
    Budget,
    Goal,
    Holding,
    Insight,
    Plan,
)
from app.db.session import engine, SessionLocal


def create_tables():
    """Create all database tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def seed_data():
    """Seed the database with sample data."""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_user = db.query(User).first()
        if existing_user:
            print("⚠️  Database already has data. Skipping seed.")
            return
        
        print("🌱 Seeding database...")
        
        # 1. Create Categories (must be first - no dependencies)
        categories = [
            Category(name="Dining", icon="🍽️", color="#FF6B6B"),
            Category(name="Shopping", icon="🛍️", color="#4ECDC4"),
            Category(name="Subscriptions", icon="📱", color="#45B7D1"),
            Category(name="Transportation", icon="🚗", color="#FFA07A"),
            Category(name="Groceries", icon="🛒", color="#98D8C8"),
            Category(name="Entertainment", icon="🎬", color="#F7DC6F"),
            Category(name="Bills", icon="💳", color="#BB8FCE"),
            Category(name="Income", icon="💰", color="#52BE80"),
        ]
        db.add_all(categories)
        db.flush()  # Get category IDs
        print(f"✅ Created {len(categories)} categories")
        
        # Get category references
        dining = next(c for c in categories if c.name == "Dining")
        shopping = next(c for c in categories if c.name == "Shopping")
        subscriptions = next(c for c in categories if c.name == "Subscriptions")
        groceries = next(c for c in categories if c.name == "Groceries")
        income = next(c for c in categories if c.name == "Income")
        
        # 2. Create User
        user = User(
            email="demo@sprout.app",
            name="Demo User",
            password_hash="$2b$12$dummy_hash_for_testing",  # In real app, use proper hashing
        )
        db.add(user)
        db.flush()  # Get user ID
        print("✅ Created user: demo@sprout.app")
        
        # 3. Create Accounts
        accounts = [
            Account(
                user_id=user.id,
                name="Chase Checking",
                account_type="checking",
                provider="Chase",
                account_num="****1234",
                balance=Decimal("5420.50"),
                is_active=True,
            ),
            Account(
                user_id=user.id,
                name="Chase Savings",
                account_type="savings",
                provider="Chase",
                account_num="****5678",
                balance=Decimal("15000.00"),
                is_active=True,
            ),
            Account(
                user_id=user.id,
                name="Chase Credit Card",
                account_type="credit_card",
                provider="Chase",
                account_num="****9012",
                balance=Decimal("-1250.75"),  # Negative for credit card
                is_active=True,
            ),
        ]
        db.add_all(accounts)
        db.flush()  # Get account IDs
        print(f"✅ Created {len(accounts)} accounts")
        
        checking = accounts[0]
        savings = accounts[1]
        credit_card = accounts[2]
        
        # 4. Create Transactions
        today = date.today()
        transactions = [
            # Income
            Transaction(
                user_id=user.id,
                account_id=checking.id,
                category_id=income.id,
                amount=Decimal("5000.00"),  # Positive for income
                date=today.replace(day=1),  # First of month
                description="Salary - Tech Corp",
                normalized_merchant="Tech Corp",
                is_subscription=False,
            ),
            # Expenses
            Transaction(
                user_id=user.id,
                account_id=checking.id,
                category_id=dining.id,
                amount=Decimal("-45.50"),  # Negative for expense
                date=today - timedelta(days=5),
                description="Starbucks Coffee",
                normalized_merchant="Starbucks",
                is_subscription=False,
                tags=["coffee", "morning"],
            ),
            Transaction(
                user_id=user.id,
                account_id=checking.id,
                category_id=dining.id,
                amount=Decimal("-89.20"),
                date=today - timedelta(days=3),
                description="Olive Garden",
                normalized_merchant="Olive Garden",
                is_subscription=False,
            ),
            Transaction(
                user_id=user.id,
                account_id=credit_card.id,
                category_id=shopping.id,
                amount=Decimal("-250.00"),
                date=today - timedelta(days=7),
                description="Amazon Purchase",
                normalized_merchant="Amazon",
                is_subscription=False,
                tags=["online", "electronics"],
            ),
            Transaction(
                user_id=user.id,
                account_id=checking.id,
                category_id=subscriptions.id,
                amount=Decimal("-14.99"),
                date=today - timedelta(days=10),
                description="Netflix Monthly",
                normalized_merchant="Netflix",
                is_subscription=True,
            ),
            Transaction(
                user_id=user.id,
                account_id=checking.id,
                category_id=groceries.id,
                amount=Decimal("-125.30"),
                date=today - timedelta(days=2),
                description="Whole Foods",
                normalized_merchant="Whole Foods",
                is_subscription=False,
            ),
        ]
        db.add_all(transactions)
        db.flush()
        print(f"✅ Created {len(transactions)} transactions")
        
        # 5. Create Budgets (for current month)
        current_month = datetime.now().month
        current_year = datetime.now().year
        budgets = [
            Budget(
                user_id=user.id,
                category_id=dining.id,
                amount=Decimal("300.00"),
                month=current_month,
                year=current_year,
                is_auto_generated=True,
            ),
            Budget(
                user_id=user.id,
                category_id=shopping.id,
                amount=Decimal("500.00"),
                month=current_month,
                year=current_year,
                is_auto_generated=True,
            ),
            Budget(
                user_id=user.id,
                category_id=groceries.id,
                amount=Decimal("400.00"),
                month=current_month,
                year=current_year,
                is_auto_generated=True,
            ),
        ]
        db.add_all(budgets)
        db.flush()
        print(f"✅ Created {len(budgets)} budgets")
        
        # 6. Create Goals
        goals = [
            Goal(
                user_id=user.id,
                name="Emergency Fund",
                target_amount=Decimal("20000.00"),
                current_amount=Decimal("15000.00"),
                target_date=date(current_year + 1, 6, 1),
                monthly_contribution=Decimal("500.00"),
                is_active=True,
            ),
            Goal(
                user_id=user.id,
                name="Vacation to Japan",
                target_amount=Decimal("5000.00"),
                current_amount=Decimal("1200.00"),
                target_date=date(current_year + 1, 12, 1),
                monthly_contribution=Decimal("300.00"),
                is_active=True,
            ),
        ]
        db.add_all(goals)
        db.flush()
        print(f"✅ Created {len(goals)} goals")
        
        # 7. Create Holdings (investments)
        holdings = [
            Holding(
                user_id=user.id,
                account_id=savings.id,
                symbol="AAPL",
                name="Apple Inc.",
                asset_type="stock",
                quantity=Decimal("10.0"),
                current_price=Decimal("175.50"),
                total_value=Decimal("1755.00"),
                cost_basis=Decimal("1500.00"),
                last_updated=datetime.now(),
            ),
            Holding(
                user_id=user.id,
                account_id=savings.id,
                symbol="VTI",
                name="Vanguard Total Stock Market ETF",
                asset_type="etf",
                quantity=Decimal("25.0"),
                current_price=Decimal("245.30"),
                total_value=Decimal("6132.50"),
                cost_basis=Decimal("6000.00"),
                last_updated=datetime.now(),
            ),
        ]
        db.add_all(holdings)
        db.flush()
        print(f"✅ Created {len(holdings)} holdings")
        
        # 8. Create Insights
        # NOTE: JSON fields cannot store Decimal directly, so we convert to strings
        insights = [
            Insight(
                user_id=user.id,
                insight_type="spending_trend",
                title="Dining spending up 18%",
                description="Your dining expenses increased by 18% compared to last month. Consider reviewing your restaurant visits.",
                raw_data={
                    "category": "Dining",
                    "increase_percent": 18,
                    "amount": "134.70",  # Decimal -> string for JSON
                },
                severity="warning",
                related_category_id=dining.id,
                is_read=False,
            ),
            Insight(
                user_id=user.id,
                insight_type="subscription_change",
                title="Netflix subscription detected",
                description="We detected a recurring Netflix charge. This subscription costs $14.99/month.",
                raw_data={
                    "merchant": "Netflix",
                    "amount": "14.99",  # Decimal -> string for JSON
                    "frequency": "monthly",
                },
                severity="info",
                is_read=False,
            ),
        ]
        db.add_all(insights)
        db.flush()
        print(f"✅ Created {len(insights)} insights")
        
        # 9. Create Plan
        plan = Plan(
            user_id=user.id,
            month=current_month,
            year=current_year,
            summary_text="Based on your spending patterns, we recommend reducing dining expenses by $50/month and increasing your emergency fund contribution to $600/month.",
            recommended_budgets=[
                {"category": "Dining", "amount": 250.00},
                {"category": "Shopping", "amount": 450.00},
            ],
            recommended_goal_contributions=[
                {"goal": "Emergency Fund", "amount": 600.00},
                {"goal": "Vacation to Japan", "amount": 300.00},
            ],
            action_items=[
                "Reduce dining out by 2 times per month",
                "Review subscription services",
                "Increase emergency fund contribution",
            ],
            is_active=True,
        )
        db.add(plan)
        db.flush()
        print("✅ Created 1 plan")
        
        # Commit everything
        db.commit()
        print("\n🎉 Database seeded successfully!")
        print(f"   User: {user.email}")
        print(f"   Accounts: {len(accounts)}")
        print(f"   Transactions: {len(transactions)}")
        print(f"   Categories: {len(categories)}")
        print(f"   Budgets: {len(budgets)}")
        print(f"   Goals: {len(goals)}")
        print(f"   Holdings: {len(holdings)}")
        print(f"   Insights: {len(insights)}")
        print(f"   Plans: 1")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Starting database seed...")
    create_tables()
    seed_data()

