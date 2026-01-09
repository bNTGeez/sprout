from datetime import date
from decimal import Decimal
import pytest

from app.db.models import Account, Category, Holding, Transaction

def test_dashboard_empty_state(authed_client, db_session, test_user):
  """
  Tests:
  - endpoint working w/ auth + db dependency overrides
  - empty user data returns valid response 
  - numbers default to 0 and lists default to []
  """

  res = authed_client.get("/api/dashboard")
  assert res.status_code == 200

  data = res.json()
  # Basic response contract
  assert set(data.keys()) == {
    "income",
    "expenses",
    "savings",
    "assets",
    "net_worth",
    "spending_breakdown",
    "recent_transactions",
  }
  assert Decimal(data["income"]) == Decimal("0")
  assert Decimal(data["expenses"]) == Decimal("0")
  assert Decimal(data["savings"]) == Decimal("0")
  assert Decimal(data["assets"]) == Decimal("0")
  assert Decimal(data["net_worth"]) == Decimal("0")
  assert data["spending_breakdown"] == []
  assert data["recent_transactions"] == []

def test_dashboard_with_data(authed_client, db_session, test_user):
  """
  Tests:
  - income/expenses for current month
  - assets include account balances and holdings
  - liabilities include credit card debt
  - spending breakdown grouped by category
  - recent transactions include type field income/expense 
  """
  today = date.today()

  # categories
  dining = Category(name="Dining", icon="🍽️", color="#FF5733")
  groceries = Category(name="Groceries", icon="🛒", color="#33FF57")
  db_session.add_all([dining, groceries])
  db_session.flush()

  checking = Account(
    user_id=test_user.id,
    name="Checking",
    account_type="checking",
    provider="Test Bank",
    account_num="1234",
    balance=Decimal("1000.00"),
    is_active=True,
  )
  savings = Account(
    user_id=test_user.id,
    name="Savings",
    account_type="savings",
    provider="Test Bank",
    account_num="5678",
    balance=Decimal("2000.00"),
    is_active=True,
  )
  credit = Account(
    user_id=test_user.id,
    name="Credit Card",
    account_type="credit_card",
    provider="Test Bank",
    account_num="9012",
    balance=Decimal("-500.00"), # Negative for credit card debt
    is_active=True,
  )
  brokerage = Account(
    user_id=test_user.id,
    name="Brokerage",
    account_type="brokerage",
    provider="Test Broker",
    account_num="3456",
    balance=Decimal("0.00"),  # Holdings tracked separately
    is_active=True,
  )
  
  db_session.add_all([checking, savings, credit, brokerage])
  db_session.flush()
  
  holding = Holding(
    user_id = test_user.id,
    account_id = brokerage.id,
    symbol = "SPY",
    total_value = Decimal("3000.00"),
  )
  
  db_session.add(holding)
  db_session.flush()

  tx_income = Transaction(
    user_id = test_user.id,
    account_id = checking.id, 
    amount = Decimal("2500.00"),
    date = today,
    description = "Salary",
    category_id = None
  ) 

  tx_dining = Transaction(
    user_id = test_user.id,
    account_id = checking.id,
    amount = Decimal("-50.00"),
    date = today,
    description = "Restaurants",
    category_id = dining.id
  )

  tx_groceries = Transaction(
    user_id = test_user.id,
    account_id = checking.id,
    amount = Decimal("-150.00"),
    date = today,
    description = "Whole Foods",
    category_id = groceries.id
  )
  db_session.add_all([tx_income, tx_dining, tx_groceries])
  db_session.commit()

  res = authed_client.get("/api/dashboard")
  assert res.status_code == 200

  data = res.json()

  assert Decimal(data["income"]) == Decimal("2500")
  assert Decimal(data["expenses"]) == Decimal("200")
  assert Decimal(data["savings"]) == Decimal("2300")

  # assets = checking+savings+brokerage + holdings_value (brokerage balance is 0 here)
  assert Decimal(data["assets"]) == Decimal("6000")  # 1000 + 2000 + 0 + 3000

  # net_worth = assets - liabilities (liabilities from credit card debt)
  assert Decimal(data["net_worth"]) == Decimal("5500")  # 6000 - 500

  assert len(data["spending_breakdown"]) == 2
  breakdown = {item["category"]: item for item in data["spending_breakdown"]}

  assert Decimal(breakdown["Dining"]["amount"]) == Decimal("50")
  assert Decimal(breakdown["Groceries"]["amount"]) == Decimal("150")

  assert breakdown["Dining"]["percentage"] == pytest.approx(round((50.0 / 200.0) * 100, 1))
  assert breakdown["Groceries"]["percentage"] == pytest.approx(round((150.0 / 200.0) * 100, 1))

  # Should have exactly our 3 transactions
  assert len(data["recent_transactions"]) == 3

  by_desc = {t["description"]: t for t in data["recent_transactions"]}
  
  # Verify our specific transactions exist with correct types
  assert "Salary" in by_desc
  assert "Restaurants" in by_desc
  assert "Whole Foods" in by_desc
  
  assert by_desc["Salary"]["type"] == "income"
  assert by_desc["Restaurants"]["type"] == "expense"
  assert by_desc["Whole Foods"]["type"] == "expense"

  # Sanity check: API returns IDs for transactions
  assert isinstance(by_desc["Salary"]["id"], int)
  assert isinstance(by_desc["Restaurants"]["id"], int)
  assert isinstance(by_desc["Whole Foods"]["id"], int)

def test_dashboard_filters_by_current_month(authed_client, db_session, test_user):
  """Tests:
  - dashboard only includes current month's income/expenses
  - previous month's transactions are excluded from calculations
  """
  today = date.today()
  
  # Create account
  checking = Account(
    user_id=test_user.id,
    name="Checking",
    account_type="checking",
    provider="Test Bank",
    account_num="1234",
    balance=Decimal("1000.00"),
    is_active=True,
  )
  db_session.add(checking)
  db_session.flush()

  # Transaction from THIS month
  tx_current = Transaction(
    user_id=test_user.id,
    account_id=checking.id,
    amount=Decimal("1000.00"),
    date=today,
    description="Current Month Income",
    category_id=None
  )

  # Transaction from LAST month (should be excluded)
  if today.month == 1:
    last_month_date = date(today.year - 1, 12, 15)
  else:
    last_month_date = date(today.year, today.month - 1, 15)
  
  tx_old = Transaction(
    user_id=test_user.id,
    account_id=checking.id,
    amount=Decimal("5000.00"),
    date=last_month_date,
    description="Last Month Income",
    category_id=None
  )

  db_session.add_all([tx_current, tx_old])
  db_session.commit()

  res = authed_client.get("/api/dashboard")
  assert res.status_code == 200

  data = res.json()
  
  # Should only include current month's $1000, not last month's $5000
  assert Decimal(data["income"]) == Decimal("1000")
  assert Decimal(data["savings"]) == Decimal("1000")

def test_dashboard_recent_transactions_ordered(authed_client, db_session, test_user):
  """Tests:
  - recent transactions are ordered by date descending (newest first)
  - limited to 10 transactions
  """
  checking = Account(
    user_id=test_user.id,
    name="Checking",
    account_type="checking",
    provider="Test Bank",
    account_num="1234",
    balance=Decimal("1000.00"),
    is_active=True,
  )
  db_session.add(checking)
  db_session.flush()

  today = date.today()
  
  # Create 12 transactions with different dates
  transactions = []
  for i in range(12):
    tx = Transaction(
      user_id=test_user.id,
      account_id=checking.id,
      amount=Decimal(f"-{i * 10}.00"),
      date=date(today.year, today.month, min(i + 1, 28)),  # Ensure valid dates
      description=f"Transaction {i}",
      category_id=None
    )
    transactions.append(tx)
  
  db_session.add_all(transactions)
  db_session.commit()

  res = authed_client.get("/api/dashboard")
  assert res.status_code == 200

  data = res.json()
  
  # Should only return 10 transactions (limit)
  assert len(data["recent_transactions"]) == 10
  
  # Should be ordered by date descending (newest first)
  # FastAPI serializes dates as ISO strings "YYYY-MM-DD", which sort correctly
  dates = [t["date"] for t in data["recent_transactions"]]  # ISO date strings
  
  # Stronger ordering assertions: newest first, oldest last (within the returned page)
  assert dates[0] == max(dates)
  assert dates[-1] == min(dates)

  # Sanity check: verify they're actually ISO date strings (YYYY-MM-DD)
  assert all(isinstance(d, str) and len(d) == 10 for d in dates)
  
  assert dates == sorted(dates, reverse=True)

def test_dashboard_requires_auth(client):
  """Dashboard is protected by auth dependency."""
  res = client.get("/api/dashboard")
  assert res.status_code in (401, 403)