"""Comprehensive tests for account API routes.

Test coverage:
1. Auth + user isolation
2. GET /api/accounts response shape and sorting
3. Plaid-linked vs manual accounts
4. Active/inactive account handling
"""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import User, Account, PlaidItem


@pytest.fixture
def user_a(db_session: Session) -> User:
    """Create User A."""
    user = User(email="user_a@example.com", name="User A", password_hash="hash_a")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user_b(db_session: Session) -> User:
    """Create User B."""
    user = User(email="user_b@example.com", name="User B", password_hash="hash_b")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def plaid_item_a(db_session: Session, user_a: User) -> PlaidItem:
    """Create PlaidItem for User A."""
    item = PlaidItem(
        user_id=user_a.id,
        plaid_item_id="test-plaid-item-a",
        access_token="test-access-token-a",
        institution_id="test-inst-a",
        institution_name="Test Bank A",
        status="good"
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def diverse_accounts_a(db_session: Session, user_a: User, plaid_item_a: PlaidItem) -> list[Account]:
    """Create diverse accounts for User A."""
    accounts = [
        # Plaid-linked accounts
        Account(
            user_id=user_a.id,
            plaid_item_id=plaid_item_a.id,
            plaid_account_id="plaid-checking-1",
            name="Chase Checking",
            account_type="checking",
            provider="Chase",
            account_num="****1234",
            balance=Decimal("5000.00"),
            is_active=True
        ),
        Account(
            user_id=user_a.id,
            plaid_item_id=plaid_item_a.id,
            plaid_account_id="plaid-savings-1",
            name="Chase Savings",
            account_type="savings",
            provider="Chase",
            account_num="****5678",
            balance=Decimal("15000.00"),
            is_active=True
        ),
        # Manual account (no Plaid)
        Account(
            user_id=user_a.id,
            plaid_item_id=None,
            plaid_account_id=None,
            name="Manual Cash",
            account_type="checking",
            provider="Manual",
            account_num="CASH",
            balance=Decimal("500.00"),
            is_active=True
        ),
        # Credit card
        Account(
            user_id=user_a.id,
            plaid_item_id=plaid_item_a.id,
            plaid_account_id="plaid-credit-1",
            name="Amex Gold",
            account_type="credit_card",
            provider="American Express",
            account_num="****9012",
            balance=Decimal("-1500.00"),
            is_active=True
        ),
        # Inactive account
        Account(
            user_id=user_a.id,
            plaid_item_id=None,
            plaid_account_id=None,
            name="Closed Account",
            account_type="checking",
            provider="Old Bank",
            account_num="****0000",
            balance=Decimal("0.00"),
            is_active=False
        ),
    ]
    
    for acc in accounts:
        db_session.add(acc)
    db_session.commit()
    for acc in accounts:
        db_session.refresh(acc)
    return accounts


@pytest.fixture
def accounts_b(db_session: Session, user_b: User) -> list[Account]:
    """Create accounts for User B."""
    accounts = [
        Account(
            user_id=user_b.id,
            name="User B Checking",
            account_type="checking",
            provider="Bank B",
            account_num="****2222",
            balance=Decimal("3000.00"),
            is_active=True
        ),
        Account(
            user_id=user_b.id,
            name="User B Savings",
            account_type="savings",
            provider="Bank B",
            account_num="****3333",
            balance=Decimal("8000.00"),
            is_active=True
        ),
    ]
    
    for acc in accounts:
        db_session.add(acc)
    db_session.commit()
    for acc in accounts:
        db_session.refresh(acc)
    return accounts


# ============================================================================
# 1. AUTH + USER ISOLATION
# ============================================================================

def test_accounts_list_requires_auth(client):
    """401 without auth header."""
    response = client.get("/api/accounts")
    assert response.status_code == 401


def test_user_isolation_list(
    app, client, db_session,
    user_a: User, user_b: User,
    diverse_accounts_a: list[Account],
    accounts_b: list[Account]
):
    """User A only sees their own accounts, not User B's."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    assert response.status_code == 200
    
    data = response.json()
    account_ids = [acc["id"] for acc in data]
    
    # Should have User A's accounts
    for acc in diverse_accounts_a:
        assert acc.id in account_ids
    
    # Should NOT have User B's accounts
    for acc in accounts_b:
        assert acc.id not in account_ids


def test_user_isolation_reverse(
    app, client, db_session,
    user_a: User, user_b: User,
    diverse_accounts_a: list[Account],
    accounts_b: list[Account]
):
    """User B only sees their own accounts, not User A's."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_b
    
    response = client.get("/api/accounts")
    assert response.status_code == 200
    
    data = response.json()
    account_ids = [acc["id"] for acc in data]
    
    # Should have User B's accounts
    for acc in accounts_b:
        assert acc.id in account_ids
    
    # Should NOT have User A's accounts
    for acc in diverse_accounts_a:
        assert acc.id not in account_ids


# ============================================================================
# 2. GET /api/accounts RESPONSE SHAPE & SORTING
# ============================================================================

def test_list_response_shape(app, client, user_a, diverse_accounts_a):
    """Response is list of account objects."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 5  # diverse_accounts_a has 5 accounts


def test_list_account_fields(authed_client, diverse_accounts_a):
    """Each account has expected fields."""
    response = authed_client.get("/api/accounts")
    data = response.json()
    
    if data:
        acc = data[0]
        required_fields = [
            "id", "user_id", "name", "account_type", 
            "provider", "balance", "is_active"
        ]
        for field in required_fields:
            assert field in acc, f"Missing field: {field}"


def test_list_field_types(authed_client, diverse_accounts_a):
    """Field types are correct."""
    response = authed_client.get("/api/accounts")
    data = response.json()
    
    if data:
        acc = data[0]
        assert isinstance(acc["id"], int)
        assert isinstance(acc["user_id"], int)
        assert isinstance(acc["name"], str)
        assert isinstance(acc["account_type"], str)
        assert isinstance(acc["provider"], str)
        assert isinstance(acc["balance"], str)  # Decimal as string
        assert isinstance(acc["is_active"], bool)


def test_list_sorted_by_name(authed_client, diverse_accounts_a):
    """Accounts are sorted by name ascending."""
    response = authed_client.get("/api/accounts")
    data = response.json()
    
    names = [acc["name"] for acc in data]
    assert names == sorted(names)


# ============================================================================
# 3. PLAID-LINKED VS MANUAL ACCOUNTS
# ============================================================================

def test_plaid_linked_accounts_returned(app, client, user_a, diverse_accounts_a, plaid_item_a):
    """Plaid-linked accounts are returned."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    plaid_linked = [acc for acc in data if "Chase" in acc["name"]]
    assert len(plaid_linked) >= 2  # Chase Checking and Chase Savings


def test_manual_accounts_returned(app, client, user_a, diverse_accounts_a):
    """Manual accounts (plaid_item_id=null) are returned."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    manual = [acc for acc in data if acc["name"] == "Manual Cash"]
    assert len(manual) == 1


def test_mixed_plaid_and_manual(app, client, user_a, diverse_accounts_a):
    """Both Plaid-linked and manual accounts appear in same list."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    # Should have both types
    has_plaid = any("Chase" in acc["name"] for acc in data)
    has_manual = any("Manual" in acc["name"] for acc in data)
    
    assert has_plaid
    assert has_manual


# ============================================================================
# 4. ACTIVE/INACTIVE ACCOUNT HANDLING
# ============================================================================

def test_inactive_accounts_returned(app, client, user_a, diverse_accounts_a):
    """Inactive accounts (is_active=false) are returned in list."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    inactive = [acc for acc in data if not acc["is_active"]]
    assert len(inactive) == 1  # "Closed Account"


def test_active_accounts_returned(app, client, user_a, diverse_accounts_a):
    """Active accounts (is_active=true) are returned."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    active = [acc for acc in data if acc["is_active"]]
    assert len(active) == 4  # All except "Closed Account"


def test_is_active_flag_accurate(app, client, user_a, diverse_accounts_a):
    """is_active flag correctly reflects DB value."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    closed = [acc for acc in data if acc["name"] == "Closed Account"]
    assert len(closed) == 1
    assert closed[0]["is_active"] is False
    
    active = [acc for acc in data if acc["name"] == "Chase Checking"]
    assert len(active) == 1
    assert active[0]["is_active"] is True


# ============================================================================
# 5. EDGE CASES
# ============================================================================

def test_empty_account_list(app, client, db_session):
    """Returns empty list when user has no accounts."""
    user = User(email="noaccounts@example.com", name="No Accounts", password_hash="hash")
    db_session.add(user)
    db_session.commit()
    
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user
    
    response = client.get("/api/accounts")
    assert response.status_code == 200
    
    data = response.json()
    assert data == []


def test_negative_balance_credit_card(app, client, user_a, diverse_accounts_a):
    """Credit card accounts can have negative balances."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    amex = [acc for acc in data if "Amex" in acc["name"]]
    assert len(amex) == 1
    assert amex[0]["balance"] == "-1500.00"  # String now
    assert amex[0]["account_type"] == "credit_card"


def test_zero_balance_account(app, client, user_a, diverse_accounts_a):
    """Accounts with zero balance are returned."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    closed = [acc for acc in data if acc["name"] == "Closed Account"]
    assert len(closed) == 1
    assert closed[0]["balance"] == "0.00"  # String now


def test_large_balance_account(app, client, user_a, diverse_accounts_a):
    """Accounts with large balances are returned correctly."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    savings = [acc for acc in data if "Savings" in acc["name"]]
    assert len(savings) >= 1
    assert savings[0]["balance"] == "15000.00"  # String now


# ============================================================================
# 6. ACCOUNT TYPES
# ============================================================================

def test_checking_account_type(app, client, user_a, diverse_accounts_a):
    """Checking accounts have correct type."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    checking = [acc for acc in data if acc["account_type"] == "checking"]
    assert len(checking) >= 2  # Chase Checking and Manual Cash


def test_savings_account_type(app, client, user_a, diverse_accounts_a):
    """Savings accounts have correct type."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    savings = [acc for acc in data if acc["account_type"] == "savings"]
    assert len(savings) == 1  # Chase Savings


def test_credit_card_account_type(app, client, user_a, diverse_accounts_a):
    """Credit card accounts have correct type."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    credit = [acc for acc in data if acc["account_type"] == "credit_card"]
    assert len(credit) == 1  # Amex Gold


def test_provider_field(app, client, user_a, diverse_accounts_a):
    """Provider field is populated correctly."""
    from app.core.auth import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user_a
    
    response = client.get("/api/accounts")
    data = response.json()
    
    providers = {acc["provider"] for acc in data}
    assert "Chase" in providers
    assert "American Express" in providers
    assert "Manual" in providers
