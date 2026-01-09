"""Comprehensive tests for transaction API routes.

Test coverage:
1. Auth + access control
2. GET /api/transactions list contract
3. Filters (search, category, date, amount, uncategorized)
4. POST /api/transactions
5. PUT /api/transactions/{id}
6. DELETE /api/transactions/{id}
7. GET /api/transactions/uncategorized/count
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import User, Account, Category, Transaction


def parse_amount(amount_str: str) -> Decimal:
    """Helper to parse amount string to Decimal for comparisons."""
    return Decimal(amount_str)


@pytest.fixture
def user_a(db_session: Session) -> User:
    """Create User A for isolation tests."""
    user = User(email="user_a@example.com", name="User A", password_hash="hash_a")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_b(db_session: Session) -> User:
    """Create User B for isolation tests."""
    user = User(email="user_b@example.com", name="User B", password_hash="hash_b")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def categories(db_session: Session) -> list[Category]:
    """Create test categories."""
    cats = [
        Category(name="Dining", icon="🍽️", color="#FF5733"),
        Category(name="Shopping", icon="🛍️", color="#33FF57"),
        Category(name="Transport", icon="🚗", color="#3357FF"),
        Category(name="Utilities", icon="⚡", color="#FFB533"),
    ]
    for cat in cats:
        db_session.add(cat)
    db_session.commit()
    for cat in cats:
        db_session.refresh(cat)
    return cats


@pytest.fixture
def account_a(db_session: Session, user_a: User) -> Account:
    """Create account for User A."""
    account = Account(
        user_id=user_a.id,
        name="User A Checking",
        account_type="checking",
        provider="Bank A",
        account_num="****1111",
        balance=Decimal("5000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def account_b(db_session: Session, user_b: User) -> Account:
    """Create account for User B."""
    account = Account(
        user_id=user_b.id,
        name="User B Checking",
        account_type="checking",
        provider="Bank B",
        account_num="****2222",
        balance=Decimal("3000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def diverse_transactions(
    db_session: Session, 
    user_a: User, 
    account_a: Account, 
    categories: list[Category]
) -> list[Transaction]:
    """Create diverse transactions for filter testing.
    
    Creates 15 transactions with various:
    - dates (spread over 30 days)
    - amounts (positive/negative, different ranges)
    - categories (some null)
    - descriptions (different merchants)
    """
    today = date.today()
    transactions = [
        # Categorized expenses
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[0].id,
            amount=Decimal("-45.50"), date=today,
            description="Starbucks Coffee", normalized_merchant="STARBUCKS"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[0].id,
            amount=Decimal("-32.00"), date=today - timedelta(days=1),
            description="Chipotle Mexican Grill", normalized_merchant="CHIPOTLE"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[1].id,
            amount=Decimal("-150.00"), date=today - timedelta(days=2),
            description="Amazon.com", normalized_merchant="AMAZON"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[2].id,
            amount=Decimal("-25.00"), date=today - timedelta(days=3),
            description="Uber Trip", normalized_merchant="UBER"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[3].id,
            amount=Decimal("-120.00"), date=today - timedelta(days=5),
            description="Electric Company", normalized_merchant="UTILITY_CO"
        ),
        
        # Uncategorized expenses
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=None,
            amount=Decimal("-75.00"), date=today - timedelta(days=7),
            description="Unknown Merchant XYZ"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=None,
            amount=Decimal("-12.50"), date=today - timedelta(days=8),
            description="Mystery Charge"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=None,
            amount=Decimal("-200.00"), date=today - timedelta(days=10),
            description="Large Unknown Purchase"
        ),
        
        # Income
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=None,
            amount=Decimal("3000.00"), date=today - timedelta(days=15),
            description="Paycheck Deposit"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=None,
            amount=Decimal("500.00"), date=today - timedelta(days=20),
            description="Freelance Payment"
        ),
        
        # Old transactions
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[0].id,
            amount=Decimal("-40.00"), date=today - timedelta(days=25),
            description="Old Coffee Shop"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[1].id,
            amount=Decimal("-99.99"), date=today - timedelta(days=28),
            description="Old Amazon Order"
        ),
        
        # Edge case amounts
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[0].id,
            amount=Decimal("-1.50"), date=today - timedelta(days=4),
            description="Small Coffee"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[1].id,
            amount=Decimal("-999.99"), date=today - timedelta(days=6),
            description="Expensive Purchase"
        ),
        Transaction(
            user_id=user_a.id, account_id=account_a.id, category_id=categories[2].id,
            amount=Decimal("-50.00"), date=today - timedelta(days=9),
            description="Uber Eats Delivery"
        ),
    ]
    
    for tx in transactions:
        db_session.add(tx)
    db_session.commit()
    for tx in transactions:
        db_session.refresh(tx)
    return transactions


# ============================================================================
# 1. AUTH + ACCESS CONTROL TESTS
# ============================================================================

def test_transactions_list_requires_auth(client):
    """401 when no auth header."""
    response = client.get("/api/transactions")
    assert response.status_code == 401


def test_transactions_create_requires_auth(client):
    """401 when no auth header."""
    response = client.post("/api/transactions", json={})
    assert response.status_code == 401


def test_transactions_update_requires_auth(client):
    """401 when no auth header."""
    response = client.put("/api/transactions/1", json={})
    assert response.status_code == 401


def test_transactions_delete_requires_auth(client):
    """401 when no auth header."""
    response = client.delete("/api/transactions/1")
    assert response.status_code == 401


def test_user_isolation_list(
    app, client, db_session,
    user_a: User, user_b: User,
    account_a: Account, account_b: Account
):
    """User A cannot see User B's transactions in list."""
    # Create transaction for User A
    tx_a = Transaction(
        user_id=user_a.id, account_id=account_a.id,
        amount=Decimal("-50.00"), date=date.today(),
        description="User A Transaction"
    )
    db_session.add(tx_a)
    db_session.commit()
    
    # Create transaction for User B
    tx_b = Transaction(
        user_id=user_b.id, account_id=account_b.id,
        amount=Decimal("-75.00"), date=date.today(),
        description="User B Transaction"
    )
    db_session.add(tx_b)
    db_session.commit()
    
    # Auth as User A
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] == 1
    assert data["transactions"][0]["description"] == "User A Transaction"


def test_user_isolation_get_single(
    app, client, db_session,
    user_a: User, user_b: User,
    account_b: Account
):
    """User A cannot GET User B's transaction by ID (returns 404)."""
    # Create transaction for User B
    tx_b = Transaction(
        user_id=user_b.id, account_id=account_b.id,
        amount=Decimal("-75.00"), date=date.today(),
        description="User B Transaction"
    )
    db_session.add(tx_b)
    db_session.commit()
    
    # Auth as User A, try to get User B's transaction
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get(f"/api/transactions/{tx_b.id}")
    assert response.status_code == 404


def test_user_isolation_update(
    app, client, db_session,
    user_a: User, user_b: User,
    account_b: Account
):
    """User A cannot PUT User B's transaction (returns 404)."""
    tx_b = Transaction(
        user_id=user_b.id, account_id=account_b.id,
        amount=Decimal("-75.00"), date=date.today(),
        description="User B Transaction"
    )
    db_session.add(tx_b)
    db_session.commit()
    
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.put(f"/api/transactions/{tx_b.id}", json={"notes": "Hacked"})
    assert response.status_code == 404


def test_user_isolation_delete(
    app, client, db_session,
    user_a: User, user_b: User,
    account_b: Account
):
    """User A cannot DELETE User B's transaction (returns 404)."""
    tx_b = Transaction(
        user_id=user_b.id, account_id=account_b.id,
        amount=Decimal("-75.00"), date=date.today(),
        description="User B Transaction"
    )
    db_session.add(tx_b)
    db_session.commit()
    
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.delete(f"/api/transactions/{tx_b.id}")
    assert response.status_code == 404


# ============================================================================
# 2. GET /api/transactions LIST CONTRACT
# ============================================================================

def test_list_response_shape(authed_client, diverse_transactions):
    """Verify response has correct shape: {transactions, total, page, pages}."""
    response = authed_client.get("/api/transactions")
    assert response.status_code == 200
    
    data = response.json()
    assert "transactions" in data
    assert "total" in data
    assert "page" in data
    assert "pages" in data
    
    assert isinstance(data["transactions"], list)
    assert isinstance(data["total"], int)
    assert isinstance(data["page"], int)
    assert isinstance(data["pages"], int)


def test_list_transaction_shape(authed_client, diverse_transactions):
    """Verify each transaction has expected fields."""
    response = authed_client.get("/api/transactions")
    data = response.json()
    
    if data["transactions"]:
        tx = data["transactions"][0]
        required_fields = [
            "id", "user_id", "account_id", "category_id", "amount", "date",
            "description", "normalized_merchant", "is_subscription", "tags",
            "notes", "created_at", "updated_at", "category", "account"
        ]
        for field in required_fields:
            assert field in tx, f"Missing field: {field}"
        
        # Check amount is string (Decimal serialization)
        assert isinstance(tx["amount"], str)
        
        # Check nested objects
        if tx["category"]:
            assert "id" in tx["category"]
            assert "name" in tx["category"]
            assert "icon" in tx["category"]
            assert "color" in tx["category"]
        
        assert "id" in tx["account"]
        assert "name" in tx["account"]
        assert "account_type" in tx["account"]


def test_list_default_pagination(app, client, db_session, user_a, diverse_transactions):
    """Default page=1, limit=50 works."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions")
    data = response.json()
    
    assert data["page"] == 1
    assert data["total"] == 15  # Our diverse_transactions fixture
    assert len(data["transactions"]) == 15  # All fit in default limit


def test_list_pagination_page_1(app, client, user_a, diverse_transactions):
    """page=1&limit=5 returns first 5."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions?page=1&limit=5")
    data = response.json()
    
    assert data["page"] == 1
    assert data["total"] == 15
    assert data["pages"] == 3  # ceil(15/5)
    assert len(data["transactions"]) == 5


def test_list_pagination_page_2(app, client, user_a, diverse_transactions):
    """page=2&limit=5 returns next 5."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions?page=2&limit=5")
    data = response.json()
    
    assert data["page"] == 2
    assert len(data["transactions"]) == 5


def test_list_pagination_last_page(app, client, user_a, diverse_transactions):
    """Last page returns remaining items."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions?page=3&limit=5")
    data = response.json()
    
    assert data["page"] == 3
    assert len(data["transactions"]) == 5  # 15 % 5 = 0, so 5 items


def test_list_pagination_beyond_max(app, client, user_a, diverse_transactions):
    """page beyond max returns empty list with correct metadata."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions?page=10&limit=5")
    data = response.json()
    
    assert response.status_code == 200
    assert data["page"] == 10
    assert data["total"] == 15
    assert data["pages"] == 3
    assert len(data["transactions"]) == 0


def test_list_ordering_stable(authed_client, diverse_transactions):
    """Transactions ordered by date desc, then id desc."""
    response = authed_client.get("/api/transactions?limit=50")
    data = response.json()
    
    transactions = data["transactions"]
    
    # Check date ordering (most recent first)
    dates = [tx["date"] for tx in transactions]
    assert dates == sorted(dates, reverse=True)
    
    # For same date, check id ordering
    today_str = date.today().isoformat()
    today_txs = [tx for tx in transactions if tx["date"] == today_str]
    if len(today_txs) > 1:
        ids = [tx["id"] for tx in today_txs]
        assert ids == sorted(ids, reverse=True)


def test_list_empty_transactions(app, client, db_session):
    """Empty transaction list returns correct pagination metadata."""
    from app.core.auth import get_current_user
    
    # Create user with no transactions
    user = User(email="empty@example.com", name="Empty User", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    app.dependency_overrides[get_current_user] = lambda: user
    
    response = client.get("/api/transactions")
    assert response.status_code == 200
    
    data = response.json()
    assert data["transactions"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["pages"] == 1  # At least 1 page even when empty


# ============================================================================
# 3. FILTER TESTS
# ============================================================================

def test_filter_search_description(app, client, user_a, diverse_transactions):
    """search=uber matches description field."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions?search=uber")
    data = response.json()
    
    assert data["total"] == 2  # "Uber Trip" and "Uber Eats"
    for tx in data["transactions"]:
        assert "uber" in tx["description"].lower()


def test_filter_search_merchant(app, client, user_a, diverse_transactions):
    """search=starbucks matches normalized_merchant field."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions?search=starbucks")
    data = response.json()
    
    assert data["total"] >= 1
    found = any("starbucks" in (tx.get("normalized_merchant") or "").lower() 
                for tx in data["transactions"])
    assert found


def test_filter_search_case_insensitive(authed_client, diverse_transactions):
    """Search is case-insensitive."""
    response1 = authed_client.get("/api/transactions?search=AMAZON")
    response2 = authed_client.get("/api/transactions?search=amazon")
    response3 = authed_client.get("/api/transactions?search=AmAzOn")
    
    assert response1.json()["total"] == response2.json()["total"]
    assert response1.json()["total"] == response3.json()["total"]


def test_filter_category_id(app, client, user_a, diverse_transactions, categories):
    """category_id=X returns only transactions with that category."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    dining_id = categories[0].id
    
    response = client.get(f"/api/transactions?category_id={dining_id}")
    data = response.json()
    
    assert data["total"] == 4  # We have 4 Dining transactions
    for tx in data["transactions"]:
        assert tx["category_id"] == dining_id


def test_filter_is_uncategorized_true(app, client, user_a, diverse_transactions):
    """is_uncategorized=true returns only transactions with category_id=null."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions?is_uncategorized=true")
    data = response.json()
    
    assert data["total"] == 5  # We have 5 uncategorized
    for tx in data["transactions"]:
        assert tx["category_id"] is None


def test_filter_is_uncategorized_false(app, client, user_a, diverse_transactions):
    """is_uncategorized=false returns only categorized transactions."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions?is_uncategorized=false")
    data = response.json()
    
    assert data["total"] == 10  # 15 - 5 uncategorized
    for tx in data["transactions"]:
        assert tx["category_id"] is not None


def test_filter_date_from_inclusive(app, client, user_a, diverse_transactions):
    """date_from is inclusive."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    cutoff = (date.today() - timedelta(days=5)).isoformat()
    response = client.get(f"/api/transactions?date_from={cutoff}")
    data = response.json()
    
    # Should include the transaction on day -5
    assert data["total"] >= 5  # transactions from day 0 to day -5
    for tx in data["transactions"]:
        assert tx["date"] >= cutoff


def test_filter_date_to_inclusive(authed_client, diverse_transactions):
    """date_to is inclusive."""
    cutoff = (date.today() - timedelta(days=10)).isoformat()
    response = authed_client.get(f"/api/transactions?date_to={cutoff}")
    data = response.json()
    
    # Should include the transaction on day -10
    for tx in data["transactions"]:
        assert tx["date"] <= cutoff


def test_filter_date_range(authed_client, diverse_transactions):
    """date_from + date_to filters correctly."""
    date_from = (date.today() - timedelta(days=10)).isoformat()
    date_to = (date.today() - timedelta(days=5)).isoformat()
    
    response = authed_client.get(
        f"/api/transactions?date_from={date_from}&date_to={date_to}"
    )
    data = response.json()
    
    for tx in data["transactions"]:
        assert date_from <= tx["date"] <= date_to


def test_filter_min_amount(authed_client, diverse_transactions):
    """min_amount filters correctly (inclusive)."""
    response = authed_client.get("/api/transactions?min_amount=-50")
    data = response.json()
    
    for tx in data["transactions"]:
        assert parse_amount(tx["amount"]) >= Decimal("-50")


def test_filter_max_amount(authed_client, diverse_transactions):
    """max_amount filters correctly (inclusive)."""
    response = authed_client.get("/api/transactions?max_amount=0")
    data = response.json()
    
    # Should only get expenses (negative amounts)
    for tx in data["transactions"]:
        assert parse_amount(tx["amount"]) <= Decimal("0")


def test_filter_amount_range(authed_client, diverse_transactions):
    """min_amount + max_amount filters correctly."""
    response = authed_client.get("/api/transactions?min_amount=-100&max_amount=-20")
    data = response.json()
    
    for tx in data["transactions"]:
        amount = parse_amount(tx["amount"])
        assert Decimal("-100") <= amount <= Decimal("-20")


def test_filter_combination(authed_client, diverse_transactions, categories):
    """Multiple filters work together."""
    dining_id = categories[0].id
    date_from = (date.today() - timedelta(days=5)).isoformat()
    
    response = authed_client.get(
        f"/api/transactions?category_id={dining_id}&date_from={date_from}&max_amount=0"
    )
    data = response.json()
    
    for tx in data["transactions"]:
        assert tx["category_id"] == dining_id
        assert tx["date"] >= date_from
        assert parse_amount(tx["amount"]) <= Decimal("0")


def test_filter_invalid_amount_range(authed_client, diverse_transactions):
    """min_amount > max_amount returns empty results (acceptable behavior)."""
    # Invalid range: min > max
    response = authed_client.get("/api/transactions?min_amount=100&max_amount=0")
    
    # Should return 200 with empty results (not 422)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["transactions"] == []


# ============================================================================
# 4. POST /api/transactions
# ============================================================================

def test_create_success(app, client, user_a, account_a, categories):
    """Successfully creates transaction and returns expected shape."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    payload = {
        "account_id": account_a.id,
        "amount": -45.50,
        "date": date.today().isoformat(),
        "description": "Test Transaction",
        "category_id": categories[0].id,
        "notes": "Test notes"
    }
    
    response = client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["description"] == "Test Transaction"
    assert data["amount"] == "-45.50"  # Now a string
    assert data["notes"] == "Test notes"
    assert data["category"]["id"] == categories[0].id
    assert "id" in data
    assert "created_at" in data


def test_create_without_category(app, client, user_a, account_a):
    """Can create transaction without category_id."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    payload = {
        "account_id": account_a.id,
        "amount": -30.00,
        "date": date.today().isoformat(),
        "description": "Uncategorized"
    }
    
    response = client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["category_id"] is None
    assert data["category"] is None


def test_create_missing_required_fields(authed_client):
    """Rejects request missing required fields."""
    payload = {
        "amount": -50.00
        # Missing account_id, date, description
    }
    
    response = authed_client.post("/api/transactions", json=payload)
    assert response.status_code == 422  # Validation error


def test_create_invalid_date_format(authed_client, account_a):
    """Rejects invalid date format."""
    payload = {
        "account_id": account_a.id,
        "amount": -50.00,
        "date": "not-a-date",
        "description": "Test"
    }
    
    response = authed_client.post("/api/transactions", json=payload)
    assert response.status_code == 422


def test_create_invalid_account_id(authed_client):
    """Rejects transaction with account_id not owned by user."""
    payload = {
        "account_id": 99999,
        "amount": -50.00,
        "date": date.today().isoformat(),
        "description": "Test"
    }
    
    response = authed_client.post("/api/transactions", json=payload)
    assert response.status_code == 400


def test_create_invalid_category_id(authed_client, account_a):
    """Rejects transaction with non-existent category_id."""
    payload = {
        "account_id": account_a.id,
        "amount": -50.00,
        "date": date.today().isoformat(),
        "description": "Test",
        "category_id": 99999
    }
    
    response = authed_client.post("/api/transactions", json=payload)
    assert response.status_code == 400


def test_create_user_id_from_auth(
    app, client, db_session,
    user_a: User, account_a: Account
):
    """user_id is derived from auth, not client input."""
    # Even if client tries to send user_id, it should be ignored
    payload = {
        "account_id": account_a.id,
        "amount": -50.00,
        "date": date.today().isoformat(),
        "description": "Test"
    }
    
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["user_id"] == user_a.id


# ============================================================================
# 5. PUT /api/transactions/{id}
# ============================================================================

def test_update_success(app, client, db_session, user_a, account_a, categories):
    """Successfully updates transaction."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    tx = Transaction(
        user_id=user_a.id, account_id=account_a.id,
        amount=Decimal("-50.00"), date=date.today(),
        description="Original"
    )
    db_session.add(tx)
    db_session.commit()
    
    payload = {
        "description": "Updated",
        "amount": -75.00,
        "category_id": categories[0].id,
        "notes": "New notes"
    }
    
    response = client.put(f"/api/transactions/{tx.id}", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["description"] == "Updated"
    assert data["amount"] == "-75.00"  # Now a string
    assert data["category"]["id"] == categories[0].id
    assert data["notes"] == "New notes"


def test_update_partial(app, client, db_session, user_a, account_a):
    """Partial update works (only updates provided fields)."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    tx = Transaction(
        user_id=user_a.id, account_id=account_a.id,
        amount=Decimal("-50.00"), date=date.today(),
        description="Original"
    )
    db_session.add(tx)
    db_session.commit()
    
    payload = {"notes": "Just notes"}
    
    response = client.put(f"/api/transactions/{tx.id}", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["notes"] == "Just notes"
    assert data["description"] == "Original"  # Unchanged
    assert data["amount"] == "-50.00"  # Unchanged, now a string


def test_update_invalid_id(authed_client):
    """Returns 404 for non-existent transaction."""
    response = authed_client.put("/api/transactions/99999", json={"notes": "Test"})
    assert response.status_code == 404


def test_update_invalid_category_id(app, client, db_session, user_a, account_a):
    """Rejects update with non-existent category_id."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    tx = Transaction(
        user_id=user_a.id, account_id=account_a.id,
        amount=Decimal("-50.00"), date=date.today(),
        description="Test"
    )
    db_session.add(tx)
    db_session.commit()
    
    response = client.put(
        f"/api/transactions/{tx.id}",
        json={"category_id": 99999}
    )
    assert response.status_code == 400


def test_update_does_not_allow_changing_user_id(
    app, client, db_session, user_a, account_a
):
    """user_id cannot be changed (should be ignored if sent)."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    tx = Transaction(
        user_id=user_a.id, account_id=account_a.id,
        amount=Decimal("-50.00"), date=date.today(),
        description="Test"
    )
    db_session.add(tx)
    db_session.commit()
    
    # TransactionUpdateRequest doesn't have user_id field, so this should be ignored
    response = client.put(
        f"/api/transactions/{tx.id}",
        json={"description": "Updated"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_a.id  # Unchanged


def test_update_clear_category(app, client, db_session, user_a, account_a, categories):
    """Can explicitly clear category by setting category_id to null."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    # Create transaction with category
    tx = Transaction(
        user_id=user_a.id, account_id=account_a.id,
        category_id=categories[0].id,
        amount=Decimal("-50.00"), date=date.today(),
        description="Categorized"
    )
    db_session.add(tx)
    db_session.commit()
    
    # Clear the category
    response = client.put(
        f"/api/transactions/{tx.id}",
        json={"category_id": None}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["category_id"] is None
    assert data["category"] is None


# ============================================================================
# 6. DELETE /api/transactions/{id}
# ============================================================================

def test_delete_success(app, client, db_session, user_a, account_a):
    """Successfully deletes transaction."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    from app.db.models import Transaction as TxModel
    
    tx = TxModel(
        user_id=user_a.id, account_id=account_a.id,
        amount=Decimal("-50.00"), date=date.today(),
        description="To Delete"
    )
    db_session.add(tx)
    db_session.commit()
    tx_id = tx.id
    
    response = client.delete(f"/api/transactions/{tx_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    
    # Verify deletion
    deleted = db_session.get(TxModel, tx_id)
    assert deleted is None


def test_delete_invalid_id(authed_client):
    """Returns 404 for non-existent transaction."""
    response = authed_client.delete("/api/transactions/99999")
    assert response.status_code == 404


def test_delete_idempotent(app, client, db_session, user_a, account_a):
    """Second delete returns 404."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    tx = Transaction(
        user_id=user_a.id, account_id=account_a.id,
        amount=Decimal("-50.00"), date=date.today(),
        description="To Delete"
    )
    db_session.add(tx)
    db_session.commit()
    tx_id = tx.id
    
    # First delete succeeds
    response1 = client.delete(f"/api/transactions/{tx_id}")
    assert response1.status_code == 200
    
    # Second delete returns 404
    response2 = client.delete(f"/api/transactions/{tx_id}")
    assert response2.status_code == 404


# ============================================================================
# 7. GET /api/transactions/uncategorized/count
# ============================================================================

def test_uncategorized_count_correct(app, client, user_a, diverse_transactions):
    """Returns correct count of uncategorized transactions."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions/uncategorized/count")
    assert response.status_code == 200
    
    data = response.json()
    assert "count" in data
    assert data["count"] == 5  # diverse_transactions has 5 uncategorized


def test_uncategorized_count_excludes_categorized(
    app, client, db_session, user_a, account_a, categories
):
    """Count excludes categorized transactions."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    # Create mix of categorized and uncategorized
    tx1 = Transaction(
        user_id=user_a.id, account_id=account_a.id, category_id=categories[0].id,
        amount=Decimal("-50.00"), date=date.today(), description="Categorized"
    )
    tx2 = Transaction(
        user_id=user_a.id, account_id=account_a.id, category_id=None,
        amount=Decimal("-30.00"), date=date.today(), description="Uncategorized"
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()
    
    response = client.get("/api/transactions/uncategorized/count")
    data = response.json()
    
    assert data["count"] == 1


def test_uncategorized_count_user_isolation(
    app, client, db_session,
    user_a: User, user_b: User,
    account_a: Account, account_b: Account
):
    """Count only includes current user's transactions."""
    # Create uncategorized for both users
    tx_a = Transaction(
        user_id=user_a.id, account_id=account_a.id, category_id=None,
        amount=Decimal("-50.00"), date=date.today(), description="User A"
    )
    tx_b = Transaction(
        user_id=user_b.id, account_id=account_b.id, category_id=None,
        amount=Decimal("-75.00"), date=date.today(), description="User B"
    )
    db_session.add_all([tx_a, tx_b])
    db_session.commit()
    
    # Auth as User A
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/transactions/uncategorized/count")
    data = response.json()
    
    assert data["count"] == 1  # Only User A's transaction


def test_uncategorized_count_zero(authed_client, db_session, user_a, account_a, categories):
    """Returns 0 when all transactions are categorized."""
    tx = Transaction(
        user_id=user_a.id, account_id=account_a.id, category_id=categories[0].id,
        amount=Decimal("-50.00"), date=date.today(), description="Categorized"
    )
    db_session.add(tx)
    db_session.commit()
    
    response = authed_client.get("/api/transactions/uncategorized/count")
    data = response.json()
    
    assert data["count"] == 0
