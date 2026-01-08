"""Integration tests for Plaid API endpoints.

These tests verify the HTTP contract of each Plaid endpoint using mocked
Plaid SDK responses. No real Plaid API calls are made.
"""

import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime

from app.db.models import PlaidItem, Account, Transaction, Category


# --- Fixtures for test data ---
# Note: mock_plaid_client is now provided globally by conftest.py

@pytest.fixture
def test_category(db_session):
    """Create a test category for transactions that need FK."""
    category = Category(name="Groceries", icon="🛒", color="#FF5733")
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def test_plaid_item(db_session, test_user):
    """Create a PlaidItem for testing status/sync endpoints."""
    plaid_item = PlaidItem(
        user_id=test_user.id,
        plaid_item_id="item_test_123",
        access_token="access-sandbox-test-token",
        institution_id="ins_test",
        institution_name="Test Bank",
        status="good"
    )
    db_session.add(plaid_item)
    db_session.commit()
    db_session.refresh(plaid_item)
    return plaid_item


@pytest.fixture
def test_account(db_session, test_user, test_plaid_item):
    """Create an Account linked to test PlaidItem."""
    account = Account(
        user_id=test_user.id,
        plaid_item_id=test_plaid_item.id,
        plaid_account_id="acc_test_123",
        name="Test Checking",
        account_type="checking",
        provider="plaid",
        account_num="1234",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def test_transaction(db_session, test_user, test_account):
    """Create a Transaction for status endpoint tests."""
    transaction = Transaction(
        user_id=test_user.id,
        account_id=test_account.id,
        amount=Decimal("-25.50"),
        date=datetime(2025, 1, 5).date(),
        description="Test Transaction",
        plaid_transaction_id="tx_test_123",
        provider_tx_id="tx_test_123",
        category_id=None,
        is_subscription=False
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction


# --- Tests for GET /api/plaid/link_token/create ---

def test_create_link_token_success(authed_client, mock_plaid_client):
    """Test successful link token creation."""
    # Mock Plaid SDK response
    mock_plaid_client.link_token_create.return_value = {
        "link_token": "link-sandbox-test-token-12345"
    }
    
    response = authed_client.get("/api/plaid/link_token/create")
    
    assert response.status_code == 200
    data = response.json()
    assert "link_token" in data
    assert data["link_token"] == "link-sandbox-test-token-12345"
    
    # Verify Plaid SDK was called
    assert mock_plaid_client.link_token_create.called


def test_create_link_token_verifies_request_parameters(authed_client, mock_plaid_client, test_user):
    """Test that link token request is constructed with correct parameters."""
    mock_plaid_client.link_token_create.return_value = {
        "link_token": "link-test-token"
    }
    
    response = authed_client.get("/api/plaid/link_token/create")
    
    assert response.status_code == 200
    
    # Verify the request was called
    assert mock_plaid_client.link_token_create.called
    call_args = mock_plaid_client.link_token_create.call_args
    request = call_args[0][0]  # First positional argument is the request object
    
    # Verify request structure - check key attributes
    assert request.client_name == "Sprout Budget App"
    assert request.language == "en"
    assert request.user.client_user_id == str(test_user.id)
    
    # Verify products and country_codes are set (they're Plaid SDK objects)
    assert len(request.products) == 2
    assert len(request.country_codes) == 1


def test_create_link_token_plaid_error(authed_client, mock_plaid_client):
    """Test link token creation when Plaid API fails."""
    # Mock Plaid SDK to raise an exception
    mock_plaid_client.link_token_create.side_effect = Exception("Plaid API error")
    
    response = authed_client.get("/api/plaid/link_token/create")
    
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "Failed to create Plaid link token" in data["detail"]


def test_create_link_token_requires_auth(client, mock_plaid_client):
    """Test that endpoint requires authentication."""
    response = client.get("/api/plaid/link_token/create")
    assert response.status_code == 401  # No auth header


# --- Tests for POST /api/plaid/item/public_token/exchange ---

def test_exchange_token_success(authed_client, mock_plaid_client, db_session, test_user):
    """Test successful public token exchange with account and transaction sync."""
    # Mock Plaid exchange response
    mock_plaid_client.item_public_token_exchange.return_value = {
        "access_token": "access-sandbox-test-abc123",
        "item_id": "item_plaid_test_xyz"
    }
    
    # Mock accounts_get response
    mock_plaid_client.accounts_get.return_value = {
        "accounts": [
            {
                "account_id": "acc_test_1",
                "name": "Plaid Checking",
                "official_name": "Plaid Gold Standard 0% Interest Checking",
                "type": "depository",
                "subtype": "checking",
                "mask": "0000",
                "balances": {"current": 100.0}
            }
        ]
    }
    
    # Mock transactions_sync response
    mock_plaid_client.transactions_sync.return_value = {
        "added": [
            {
                "transaction_id": "tx_1",
                "account_id": "acc_test_1",
                "amount": 12.50,
                "date": "2025-01-05",
                "merchant_name": "Starbucks",
                "name": "Starbucks",
                "transaction_type": "debit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_abc123"
    }
    
    response = authed_client.post(
        "/api/plaid/item/public_token/exchange",
        json={
            "public_token": "public-sandbox-test-token",
            "institution_id": "ins_test",
            "institution_name": "Test Bank"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "plaid_item_id" in data
    assert data["accounts_synced"] == 1
    assert data["transactions_synced"]["added"] == 1
    
    # Verify PlaidItem created in DB
    plaid_item = db_session.query(PlaidItem).filter_by(user_id=test_user.id).first()
    assert plaid_item is not None
    assert plaid_item.plaid_item_id == "item_plaid_test_xyz"
    assert plaid_item.access_token == "access-sandbox-test-abc123"
    assert plaid_item.institution_name == "Test Bank"
    
    # Verify Account created
    account = db_session.query(Account).filter_by(plaid_account_id="acc_test_1").first()
    assert account is not None
    assert account.name == "Plaid Gold Standard 0% Interest Checking"
    assert account.account_type == "checking"
    
    # Verify Transaction created
    transaction = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_1").first()
    assert transaction is not None
    assert transaction.description == "Starbucks"
    assert transaction.amount == Decimal("-12.50")  # Debit on checking = negative


def test_exchange_token_sync_fails_gracefully(authed_client, mock_plaid_client, db_session):
    """Test that PlaidItem is still created even if transaction sync fails."""
    mock_plaid_client.item_public_token_exchange.return_value = {
        "access_token": "access-sandbox-test",
        "item_id": "item_test_fail_sync"
    }
    
    # Accounts sync succeeds
    mock_plaid_client.accounts_get.return_value = {
        "accounts": [
            {
                "account_id": "acc_1",
                "name": "Checking",
                "type": "depository",
                "subtype": "checking",
                "mask": "1234",
                "balances": {"current": 500.0}
            }
        ]
    }
    
    # Transactions sync fails
    mock_plaid_client.transactions_sync.side_effect = Exception("Transaction sync error")
    
    response = authed_client.post(
        "/api/plaid/item/public_token/exchange",
        json={
            "public_token": "public-test",
            "institution_id": "ins_test",
            "institution_name": "Test Bank"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "plaid_item_id" in data
    assert data["accounts_synced"] == 1
    # Transaction sync failure should not have result
    assert data["transactions_synced"] is None
    
    # PlaidItem should still exist
    plaid_item = db_session.query(PlaidItem).filter_by(plaid_item_id="item_test_fail_sync").first()
    assert plaid_item is not None


def test_exchange_token_plaid_error(authed_client, mock_plaid_client, db_session):
    """Test exchange endpoint when Plaid API fails."""
    mock_plaid_client.item_public_token_exchange.side_effect = Exception("Invalid public token")
    
    response = authed_client.post(
        "/api/plaid/item/public_token/exchange",
        json={
            "public_token": "invalid-token",
            "institution_id": "ins_test",
            "institution_name": "Test Bank"
        }
    )
    
    assert response.status_code == 500
    data = response.json()
    assert "Failed to exchange Plaid token" in data["detail"]
    
    # No PlaidItem should be created
    assert db_session.query(PlaidItem).count() == 0


def test_exchange_token_requires_auth(client, mock_plaid_client):
    """Test that exchange endpoint requires authentication."""
    response = client.post(
        "/api/plaid/item/public_token/exchange",
        json={"public_token": "test"}
    )
    assert response.status_code == 401


# --- Tests for GET /api/plaid/items ---

def test_list_plaid_items_empty(authed_client):
    """Test listing PlaidItems when user has none."""
    response = authed_client.get("/api/plaid/items")
    
    assert response.status_code == 200
    data = response.json()
    assert "plaid_items" in data
    assert len(data["plaid_items"]) == 0


def test_list_plaid_items_multiple(authed_client, db_session, test_user):
    """Test listing multiple PlaidItems."""
    # Create two PlaidItems
    item1 = PlaidItem(
        user_id=test_user.id,
        plaid_item_id="item_1",
        access_token="token_1",
        institution_id="ins_1",
        institution_name="Bank A",
        status="good"
    )
    item2 = PlaidItem(
        user_id=test_user.id,
        plaid_item_id="item_2",
        access_token="token_2",
        institution_id="ins_2",
        institution_name="Bank B",
        status="requires_reauth"
    )
    db_session.add_all([item1, item2])
    db_session.commit()
    
    response = authed_client.get("/api/plaid/items")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["plaid_items"]) == 2
    
    # Verify both items are present (don't rely on ordering since created_at might be same)
    institution_names = {item["institution_name"] for item in data["plaid_items"]}
    assert institution_names == {"Bank A", "Bank B"}
    
    # Verify response structure
    assert "id" in data["plaid_items"][0]
    assert "status" in data["plaid_items"][0]
    assert "created_at" in data["plaid_items"][0]


def test_list_plaid_items_requires_auth(client):
    """Test that list endpoint requires authentication."""
    response = client.get("/api/plaid/items")
    assert response.status_code == 401


# --- Tests for GET /api/plaid/status/{plaid_item_id} ---

def test_get_status_success(authed_client, test_plaid_item, test_account, test_transaction):
    """Test getting status for a PlaidItem with accounts and transactions."""
    response = authed_client.get(f"/api/plaid/status/{test_plaid_item.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["plaid_item_id"] == test_plaid_item.id
    assert data["institution_name"] == "Test Bank"
    assert data["status"] == "good"
    assert data["accounts_count"] == 1
    assert data["transactions_count"] == 1
    assert data["has_cursor"] is False  # No cursor set
    assert "last_synced" in data


def test_get_status_not_found(authed_client):
    """Test getting status for non-existent PlaidItem."""
    response = authed_client.get("/api/plaid/status/99999")
    assert response.status_code == 404
    assert "PlaidItem not found" in response.json()["detail"]


def test_get_status_unauthorized(authed_client, db_session):
    """Test that user cannot access another user's PlaidItem."""
    from app.db.models import User
    
    # Create another user and their PlaidItem
    other_user = User(email="other@example.com", name="Other", password_hash="hash")
    db_session.add(other_user)
    db_session.commit()
    
    other_item = PlaidItem(
        user_id=other_user.id,
        plaid_item_id="item_other",
        access_token="token_other",
        institution_id="ins_other",
        institution_name="Other Bank",
        status="good"
    )
    db_session.add(other_item)
    db_session.commit()
    
    # Try to access other user's item
    response = authed_client.get(f"/api/plaid/status/{other_item.id}")
    assert response.status_code == 404


def test_get_status_no_transactions(authed_client, test_plaid_item, test_account):
    """Test status when PlaidItem has accounts but no transactions."""
    response = authed_client.get(f"/api/plaid/status/{test_plaid_item.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["accounts_count"] == 1
    assert data["transactions_count"] == 0


def test_get_status_filters_null_plaid_transaction_id(authed_client, test_plaid_item, test_account, db_session):
    """Test that status only counts transactions with plaid_transaction_id set."""
    # Create one transaction WITH plaid_transaction_id
    tx_with_plaid = Transaction(
        user_id=test_account.user_id,
        account_id=test_account.id,
        amount=Decimal("-50.00"),
        date=datetime(2025, 1, 5).date(),
        description="Plaid Transaction",
        plaid_transaction_id="tx_plaid_123",
        provider_tx_id="tx_plaid_123",
        category_id=None,
        is_subscription=False
    )
    
    # Create one transaction WITHOUT plaid_transaction_id (manual entry)
    tx_without_plaid = Transaction(
        user_id=test_account.user_id,
        account_id=test_account.id,
        amount=Decimal("-25.00"),
        date=datetime(2025, 1, 6).date(),
        description="Manual Transaction",
        plaid_transaction_id=None,  # Manual entry
        provider_tx_id=None,
        category_id=None,
        is_subscription=False
    )
    
    db_session.add_all([tx_with_plaid, tx_without_plaid])
    db_session.commit()
    
    response = authed_client.get(f"/api/plaid/status/{test_plaid_item.id}")
    
    assert response.status_code == 200
    data = response.json()
    # Should only count the Plaid transaction, not the manual one
    assert data["transactions_count"] == 1


def test_get_status_filters_other_plaid_item_transactions(authed_client, db_session, test_user):
    """Test that status only counts transactions for accounts under this PlaidItem."""
    # Create first PlaidItem with account and transaction
    plaid_item_1 = PlaidItem(
        user_id=test_user.id,
        plaid_item_id="item_1",
        access_token="token_1",
        institution_id="ins_1",
        institution_name="Bank 1",
        status="good"
    )
    db_session.add(plaid_item_1)
    db_session.commit()
    
    account_1 = Account(
        user_id=test_user.id,
        plaid_item_id=plaid_item_1.id,
        plaid_account_id="acc_1",
        name="Account 1",
        account_type="checking",
        provider="plaid",
        account_num="1111",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account_1)
    db_session.commit()
    
    tx_1 = Transaction(
        user_id=test_user.id,
        account_id=account_1.id,
        amount=Decimal("-100.00"),
        date=datetime(2025, 1, 5).date(),
        description="Transaction 1",
        plaid_transaction_id="tx_1",
        provider_tx_id="tx_1",
        category_id=None,
        is_subscription=False
    )
    db_session.add(tx_1)
    db_session.commit()
    
    # Create second PlaidItem with account and transaction
    plaid_item_2 = PlaidItem(
        user_id=test_user.id,
        plaid_item_id="item_2",
        access_token="token_2",
        institution_id="ins_2",
        institution_name="Bank 2",
        status="good"
    )
    db_session.add(plaid_item_2)
    db_session.commit()
    
    account_2 = Account(
        user_id=test_user.id,
        plaid_item_id=plaid_item_2.id,
        plaid_account_id="acc_2",
        name="Account 2",
        account_type="checking",
        provider="plaid",
        account_num="2222",
        balance=Decimal("2000.00"),
        is_active=True
    )
    db_session.add(account_2)
    db_session.commit()
    
    tx_2 = Transaction(
        user_id=test_user.id,
        account_id=account_2.id,
        amount=Decimal("-200.00"),
        date=datetime(2025, 1, 6).date(),
        description="Transaction 2",
        plaid_transaction_id="tx_2",
        provider_tx_id="tx_2",
        category_id=None,
        is_subscription=False
    )
    db_session.add(tx_2)
    db_session.commit()
    
    # Get status for plaid_item_1 - should only see its own transaction
    response = authed_client.get(f"/api/plaid/status/{plaid_item_1.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["accounts_count"] == 1
    assert data["transactions_count"] == 1  # Only tx_1, not tx_2


def test_get_status_has_cursor_true(authed_client, test_plaid_item, db_session):
    """Test that has_cursor is True when cursor is set."""
    # Set a cursor on the PlaidItem
    test_plaid_item.transactions_cursor = "cursor_abc123"
    db_session.commit()
    
    response = authed_client.get(f"/api/plaid/status/{test_plaid_item.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["has_cursor"] is True


def test_get_status_requires_auth(client, test_plaid_item):
    """Test that status endpoint requires authentication."""
    response = client.get(f"/api/plaid/status/{test_plaid_item.id}")
    assert response.status_code == 401


# --- Tests for POST /api/plaid/sync ---

def test_sync_success(authed_client, mock_plaid_client, test_plaid_item, db_session):
    """Test manual sync of accounts and transactions."""
    # Mock accounts_get
    mock_plaid_client.accounts_get.return_value = {
        "accounts": [
            {
                "account_id": "acc_sync_1",
                "name": "Sync Checking",
                "type": "depository",
                "subtype": "checking",
                "mask": "5678",
                "balances": {"current": 2000.0}
            }
        ]
    }
    
    # Mock transactions_sync
    mock_plaid_client.transactions_sync.return_value = {
        "added": [
            {
                "transaction_id": "tx_sync_1",
                "account_id": "acc_sync_1",
                "amount": 50.0,
                "date": "2025-01-06",
                "merchant_name": "Target",
                "name": "Target",
                "transaction_type": "debit"
            },
            {
                "transaction_id": "tx_sync_2",
                "account_id": "acc_sync_1",
                "amount": 100.0,
                "date": "2025-01-07",
                "merchant_name": "Paycheck",
                "name": "Paycheck Deposit",
                "transaction_type": "credit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_sync_abc"
    }
    
    response = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["accounts_synced"] == 1
    assert data["transactions"]["added"] == 2
    assert data["transactions"]["modified"] == 0
    assert data["transactions"]["removed"] == 0
    
    # Verify Account created
    account = db_session.query(Account).filter_by(plaid_account_id="acc_sync_1").first()
    assert account is not None
    
    # Verify Transactions created
    tx1 = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_sync_1").first()
    assert tx1 is not None
    assert tx1.amount == Decimal("-50.0")  # Debit = expense
    
    tx2 = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_sync_2").first()
    assert tx2 is not None
    assert tx2.amount == Decimal("100.0")  # Credit = income
    
    # Verify cursor updated
    db_session.refresh(test_plaid_item)
    assert test_plaid_item.transactions_cursor == "cursor_sync_abc"


def test_sync_plaid_item_not_found(authed_client, mock_plaid_client):
    """Test sync with invalid PlaidItem ID."""
    response = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": 99999}
    )
    
    assert response.status_code == 404
    assert "PlaidItem not found" in response.json()["detail"]


def test_sync_unauthorized(authed_client, db_session):
    """Test that user cannot sync another user's PlaidItem."""
    from app.db.models import User
    
    other_user = User(email="other@example.com", name="Other", password_hash="hash")
    db_session.add(other_user)
    db_session.commit()
    
    other_item = PlaidItem(
        user_id=other_user.id,
        plaid_item_id="item_other",
        access_token="token_other",
        institution_id="ins_other",
        institution_name="Other Bank",
        status="good"
    )
    db_session.add(other_item)
    db_session.commit()
    
    response = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": other_item.id}
    )
    
    assert response.status_code == 404


def test_sync_plaid_error(authed_client, mock_plaid_client, test_plaid_item):
    """Test sync when Plaid API fails."""
    # Accounts sync succeeds
    mock_plaid_client.accounts_get.return_value = {"accounts": []}
    
    # Transactions sync fails
    mock_plaid_client.transactions_sync.side_effect = Exception("Plaid API error")
    
    response = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    
    assert response.status_code == 500
    assert "Failed to sync Plaid data" in response.json()["detail"]


def test_sync_requires_auth(client, test_plaid_item):
    """Test that sync endpoint requires authentication."""
    response = client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    assert response.status_code == 401


def test_sync_valueerror_returns_404(authed_client, test_plaid_item):
    """Test that ValueError from sync functions returns 404."""
    # Patch the service function that the route actually calls
    with patch("app.api.plaid.routes.sync_accounts") as mock_sync_accounts:
        mock_sync_accounts.side_effect = ValueError("Custom error message")
        
        response = authed_client.post(
            "/api/plaid/sync",
            params={"plaid_item_id": test_plaid_item.id}
        )
    
    assert response.status_code == 404
    assert "Custom error message" in response.json()["detail"]


def test_sync_idempotency_no_duplicate_accounts(authed_client, db_session, test_plaid_item, mock_plaid_client):
    """Test that calling /sync twice doesn't duplicate accounts."""
    # Mock Plaid response with one account
    mock_plaid_client.accounts_get.return_value = {
        "accounts": [
            {
                "account_id": "acc_idempotent",
                "name": "Test Account",
                "official_name": "Test Checking",
                "type": "depository",
                "subtype": "checking",
                "mask": "1234",
                "balances": {"current": 500.00}
            }
        ]
    }
    
    mock_plaid_client.transactions_sync.return_value = {
        "added": [],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_1"
    }
    
    # First sync
    response1 = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    assert response1.status_code == 200
    assert response1.json()["accounts_synced"] == 1
    
    # Second sync with same data
    response2 = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    assert response2.status_code == 200
    assert response2.json()["accounts_synced"] == 1  # Still 1, not 2
    
    # Verify only one account exists in DB
    from app.db.models import Account
    accounts = db_session.query(Account).filter_by(plaid_account_id="acc_idempotent").all()
    assert len(accounts) == 1


def test_sync_idempotency_no_duplicate_transactions(authed_client, db_session, test_plaid_item, mock_plaid_client):
    """Test that calling /sync twice doesn't duplicate transactions."""
    # Create an account first
    from app.db.models import Account
    account = Account(
        user_id=test_plaid_item.user_id,
        plaid_item_id=test_plaid_item.id,
        plaid_account_id="acc_tx_idem",
        name="Transaction Idempotent Test",
        account_type="checking",
        provider="plaid",
        account_num="5678",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    mock_plaid_client.accounts_get.return_value = {"accounts": []}
    
    # Mock same transaction in both syncs
    mock_plaid_client.transactions_sync.return_value = {
        "added": [
            {
                "transaction_id": "tx_idem",
                "account_id": "acc_tx_idem",
                "amount": 100.0,
                "date": "2025-01-10",
                "merchant_name": "Test Store",
                "name": "Test Store",
                "transaction_type": "debit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_tx"
    }
    
    # First sync
    response1 = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    assert response1.status_code == 200
    assert response1.json()["transactions"]["added"] == 1
    
    # Second sync with same transaction
    response2 = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    assert response2.status_code == 200
    assert response2.json()["transactions"]["added"] == 0  # Skipped duplicate
    
    # Verify only one transaction exists in DB
    from app.db.models import Transaction
    transactions = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_idem").all()
    assert len(transactions) == 1


def test_sync_cursor_persistence(authed_client, db_session, test_plaid_item, mock_plaid_client):
    """Test that /sync persists and uses cursor for incremental syncs."""
    # Create an account
    from app.db.models import Account
    account = Account(
        user_id=test_plaid_item.user_id,
        plaid_item_id=test_plaid_item.id,
        plaid_account_id="acc_cursor_persist",
        name="Cursor Persist Test",
        account_type="checking",
        provider="plaid",
        account_num="9999",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # Verify no cursor initially
    assert test_plaid_item.transactions_cursor is None
    
    mock_plaid_client.accounts_get.return_value = {"accounts": []}
    
    # First sync
    mock_plaid_client.transactions_sync.return_value = {
        "added": [
            {
                "transaction_id": "tx_cursor_1",
                "account_id": "acc_cursor_persist",
                "amount": 50.0,
                "date": "2025-01-15",
                "merchant_name": "First Sync",
                "name": "First Sync",
                "transaction_type": "debit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_after_first_sync"
    }
    
    response1 = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    assert response1.status_code == 200
    
    # Verify cursor was saved
    db_session.refresh(test_plaid_item)
    assert test_plaid_item.transactions_cursor == "cursor_after_first_sync"
    
    # Second sync - should use saved cursor
    mock_plaid_client.transactions_sync.return_value = {
        "added": [
            {
                "transaction_id": "tx_cursor_2",
                "account_id": "acc_cursor_persist",
                "amount": 75.0,
                "date": "2025-01-16",
                "merchant_name": "Second Sync",
                "name": "Second Sync",
                "transaction_type": "debit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_after_second_sync"
    }
    
    response2 = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    assert response2.status_code == 200
    
    # Verify cursor was updated
    db_session.refresh(test_plaid_item)
    assert test_plaid_item.transactions_cursor == "cursor_after_second_sync"
    
    # Verify the second sync used the first cursor
    call_args = mock_plaid_client.transactions_sync.call_args
    request = call_args[0][0]
    assert request.cursor == "cursor_after_first_sync"


def test_sync_partial_failure_accounts_succeed_transactions_fail(authed_client, db_session, test_plaid_item, mock_plaid_client):
    """Test behavior when accounts sync succeeds but transactions sync fails."""
    # Mock successful accounts sync
    mock_plaid_client.accounts_get.return_value = {
        "accounts": [
            {
                "account_id": "acc_partial",
                "name": "Partial Success Account",
                "official_name": "Partial Success",
                "type": "depository",
                "subtype": "checking",
                "mask": "0000",
                "balances": {"current": 250.00}
            }
        ]
    }
    
    # Mock failed transactions sync
    mock_plaid_client.transactions_sync.side_effect = Exception("Transactions API error")
    
    response = authed_client.post(
        "/api/plaid/sync",
        params={"plaid_item_id": test_plaid_item.id}
    )
    
    # Should return 500 since transactions failed
    assert response.status_code == 500
    assert "Failed to sync Plaid data" in response.json()["detail"]
    
    # But accounts should still be created
    from app.db.models import Account
    account = db_session.query(Account).filter_by(plaid_account_id="acc_partial").first()
    assert account is not None
    assert account.name == "Partial Success"
