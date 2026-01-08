"""Unit tests for Plaid service functions.

These tests verify the business logic in services.py (normalize_amount,
sync_accounts, sync_transactions) with mocked Plaid SDK calls.
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, date

from app.api.plaid.services import normalize_amount, sync_accounts, sync_transactions
from app.db.models import PlaidItem, Account, Transaction


# --- Tests for normalize_amount() ---

def test_normalize_amount_checking_debit():
    """Checking account debit (expense) should be negative."""
    plaid_tx = {"amount": 50.0, "transaction_type": "debit"}
    result = normalize_amount(plaid_tx, "checking")
    assert result == Decimal("-50.0")


def test_normalize_amount_checking_credit():
    """Checking account credit (income) should be positive."""
    plaid_tx = {"amount": 100.0, "transaction_type": "credit"}
    result = normalize_amount(plaid_tx, "checking")
    assert result == Decimal("100.0")


def test_normalize_amount_savings_debit():
    """Savings account debit (expense) should be negative."""
    plaid_tx = {"amount": 25.0, "transaction_type": "debit"}
    result = normalize_amount(plaid_tx, "savings")
    assert result == Decimal("-25.0")


def test_normalize_amount_savings_credit():
    """Savings account credit (income) should be positive."""
    plaid_tx = {"amount": 500.0, "transaction_type": "credit"}
    result = normalize_amount(plaid_tx, "savings")
    assert result == Decimal("500.0")


def test_normalize_amount_credit_card_debit():
    """Credit card debit (payment) should be negative (money leaving)."""
    plaid_tx = {"amount": 200.0, "transaction_type": "debit"}
    result = normalize_amount(plaid_tx, "credit_card")
    assert result == Decimal("-200.0")


def test_normalize_amount_credit_card_credit():
    """Credit card credit (charge) should be negative (expense)."""
    plaid_tx = {"amount": 75.0, "transaction_type": "credit"}
    result = normalize_amount(plaid_tx, "credit_card")
    assert result == Decimal("-75.0")


def test_normalize_amount_brokerage_debit():
    """Brokerage debit should be negative."""
    plaid_tx = {"amount": 1000.0, "transaction_type": "debit"}
    result = normalize_amount(plaid_tx, "brokerage")
    assert result == Decimal("-1000.0")


def test_normalize_amount_brokerage_credit():
    """Brokerage credit should be positive."""
    plaid_tx = {"amount": 2000.0, "transaction_type": "credit"}
    result = normalize_amount(plaid_tx, "brokerage")
    assert result == Decimal("2000.0")


def test_normalize_amount_missing_transaction_type_with_refund():
    """If transaction_type missing, infer from merchant name (refund = positive)."""
    plaid_tx = {
        "amount": 50.0,
        "transaction_type": "unknown",
        "merchant_name": "Amazon Refund"
    }
    result = normalize_amount(plaid_tx, "checking")
    assert result == Decimal("50.0")  # Refund is positive


def test_normalize_amount_missing_transaction_type_expense():
    """If transaction_type missing and no refund keyword, assume expense (negative)."""
    plaid_tx = {
        "amount": 30.0,
        "transaction_type": "unknown",
        "merchant_name": "Random Store"
    }
    result = normalize_amount(plaid_tx, "checking")
    assert result == Decimal("-30.0")


def test_normalize_amount_missing_transaction_type_refund_uppercase():
    """Refund detection should be case-insensitive (REFUND, Refund, refund)."""
    plaid_tx = {
        "amount": 50.0,
        "transaction_type": "unknown",
        "merchant_name": "REFUND FROM STORE"
    }
    result = normalize_amount(plaid_tx, "checking")
    assert result == Decimal("50.0")  # Refund = positive


def test_normalize_amount_zero():
    """Zero amount should remain zero."""
    plaid_tx = {"amount": 0.0, "transaction_type": "debit"}
    result = normalize_amount(plaid_tx, "checking")
    assert result == Decimal("0.0")


def test_normalize_amount_large_value():
    """Test with large monetary value."""
    plaid_tx = {"amount": 999999.99, "transaction_type": "credit"}
    result = normalize_amount(plaid_tx, "checking")
    assert result == Decimal("999999.99")


# --- Tests for sync_accounts() ---

@pytest.fixture
def test_plaid_item_for_services(db_session, test_user):
    """Create a PlaidItem for service function tests."""
    plaid_item = PlaidItem(
        user_id=test_user.id,
        plaid_item_id="item_service_test",
        access_token="access-service-test",
        institution_id="ins_service",
        institution_name="Service Test Bank",
        status="good"
    )
    db_session.add(plaid_item)
    db_session.commit()
    db_session.refresh(plaid_item)
    return plaid_item


def test_sync_accounts_not_found(db_session):
    """sync_accounts should raise ValueError if PlaidItem not found."""
    with pytest.raises(ValueError, match="Plaid item with id 99999 not found"):
        sync_accounts(99999, db_session)


def test_sync_accounts_creates_new_accounts(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_accounts should create new Account records from Plaid data."""
    mock_plaid_response = {
        "accounts": [
            {
                "account_id": "acc_new_1",
                "name": "My Checking",
                "official_name": "Premium Checking Account",
                "type": "depository",
                "subtype": "checking",
                "mask": "1234",
                "balances": {"current": 1500.00}
            },
            {
                "account_id": "acc_new_2",
                "name": "My Savings",
                "official_name": None,
                "type": "depository",
                "subtype": "savings",
                "mask": "5678",
                "balances": {"current": 5000.00}
            }
        ]
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.accounts_get.return_value = mock_plaid_response
    
    result = sync_accounts(test_plaid_item_for_services.id, db_session)
    
    assert len(result) == 2
    
    # Verify first account
    acc1 = db_session.query(Account).filter_by(plaid_account_id="acc_new_1").first()
    assert acc1 is not None
    assert acc1.name == "Premium Checking Account"
    assert acc1.account_type == "checking"
    assert acc1.account_num == "1234"
    assert acc1.balance == Decimal("1500.00")
    assert acc1.plaid_item_id == test_plaid_item_for_services.id
    
    # Verify second account
    acc2 = db_session.query(Account).filter_by(plaid_account_id="acc_new_2").first()
    assert acc2 is not None
    assert acc2.name == "My Savings"  # Uses name field when official_name is None
    assert acc2.account_type == "savings"


def test_sync_accounts_updates_existing(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_accounts should update existing Account if plaid_account_id matches."""
    # Create existing account
    existing = Account(
        user_id=test_plaid_item_for_services.user_id,
        plaid_item_id=test_plaid_item_for_services.id,
        plaid_account_id="acc_existing",
        name="Old Name",
        account_type="checking",
        provider="plaid",
        account_num="0000",
        balance=Decimal("100.00"),
        is_active=True
    )
    db_session.add(existing)
    db_session.commit()
    original_id = existing.id
    
    # Mock Plaid response with updated data
    mock_plaid_response = {
        "accounts": [
            {
                "account_id": "acc_existing",
                "name": "Updated Checking",
                "official_name": "Updated Official Name",
                "type": "depository",
                "subtype": "checking",
                "mask": "9999",
                "balances": {"current": 2500.00}
            }
        ]
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.accounts_get.return_value = mock_plaid_response
    
    result = sync_accounts(test_plaid_item_for_services.id, db_session)
    
    assert len(result) == 1
    
    # Verify account was updated (same ID)
    updated = db_session.query(Account).filter_by(id=original_id).first()
    assert updated is not None
    assert updated.name == "Updated Official Name"
    assert updated.account_num == "9999"
    assert updated.balance == Decimal("2500.00")
    
    # Verify no duplicate created
    all_accounts = db_session.query(Account).filter_by(plaid_account_id="acc_existing").all()
    assert len(all_accounts) == 1


def test_sync_accounts_type_mapping(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_accounts should correctly map Plaid types to app account types."""
    mock_plaid_response = {
        "accounts": [
            {
                "account_id": "acc_credit",
                "name": "Credit Card",
                "type": "credit",
                "subtype": "credit card",
                "mask": "1111",
                "balances": {"current": -500.00}
            },
            {
                "account_id": "acc_investment",
                "name": "Brokerage",
                "type": "investment",
                "subtype": "brokerage",
                "mask": "2222",
                "balances": {"current": 10000.00}
            }
        ]
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.accounts_get.return_value = mock_plaid_response
    
    result = sync_accounts(test_plaid_item_for_services.id, db_session)
    
    credit_acc = db_session.query(Account).filter_by(plaid_account_id="acc_credit").first()
    assert credit_acc.account_type == "credit_card"
    
    investment_acc = db_session.query(Account).filter_by(plaid_account_id="acc_investment").first()
    assert investment_acc.account_type == "brokerage"


def test_sync_accounts_empty_response(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_accounts should handle empty accounts array gracefully."""
    mock_plaid_response = {"accounts": []}
    
    # Configure the mock client from the fixture
    mock_plaid_client.accounts_get.return_value = mock_plaid_response
    
    result = sync_accounts(test_plaid_item_for_services.id, db_session)
    
    assert result == []


def test_sync_accounts_handles_object_response(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_accounts should handle Plaid SDK object responses (not just dicts)."""
    # Mock Plaid SDK objects (with to_dict method)
    mock_account = MagicMock()
    mock_account.to_dict.return_value = {
        "account_id": "acc_obj",
        "name": "Object Account",
        "official_name": None,
        "type": "depository",
        "subtype": "checking",
        "mask": "3333",
        "balances": {"current": 750.00}
    }
    
    mock_response = MagicMock()
    mock_response.to_dict.return_value = {"accounts": [mock_account.to_dict()]}
    
    # Configure the mock client from the fixture
    mock_plaid_client.accounts_get.return_value = mock_response.to_dict()
    
    result = sync_accounts(test_plaid_item_for_services.id, db_session)
    
    assert len(result) == 1
    acc = db_session.query(Account).filter_by(plaid_account_id="acc_obj").first()
    assert acc is not None


# --- Tests for sync_transactions() ---

def test_sync_transactions_not_found(db_session):
    """sync_transactions should raise ValueError if PlaidItem not found."""
    with pytest.raises(ValueError, match="Plaid item with id 99999 not found"):
        sync_transactions(99999, db_session)


def test_sync_transactions_adds_new(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_transactions should create new Transaction records."""
    # Create an account first
    account = Account(
        user_id=test_plaid_item_for_services.user_id,
        plaid_item_id=test_plaid_item_for_services.id,
        plaid_account_id="acc_tx_test",
        name="Transaction Test Account",
        account_type="checking",
        provider="plaid",
        account_num="4444",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # Mock Plaid transactions_sync response
    mock_response = {
        "added": [
            {
                "transaction_id": "tx_add_1",
                "account_id": "acc_tx_test",
                "amount": 45.67,
                "date": "2025-01-05",
                "merchant_name": "Coffee Shop",
                "name": "Coffee Shop",
                "transaction_type": "debit"
            },
            {
                "transaction_id": "tx_add_2",
                "account_id": "acc_tx_test",
                "amount": 1000.00,
                "date": "2025-01-06",
                "merchant_name": "Salary",
                "name": "Payroll Deposit",
                "transaction_type": "credit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_123"
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.transactions_sync.return_value = mock_response
    
    result = sync_transactions(test_plaid_item_for_services.id, db_session)
    
    assert result["added"] == 2
    assert result["modified"] == 0
    assert result["removed"] == 0
    
    # Verify transactions created
    tx1 = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_add_1").first()
    assert tx1 is not None
    assert tx1.description == "Coffee Shop"
    assert tx1.amount == Decimal("-45.67")  # Debit = negative
    assert tx1.date == date(2025, 1, 5)
    
    tx2 = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_add_2").first()
    assert tx2 is not None
    assert tx2.amount == Decimal("1000.00")  # Credit = positive
    
    # Verify cursor updated
    db_session.refresh(test_plaid_item_for_services)
    assert test_plaid_item_for_services.transactions_cursor == "cursor_123"


def test_sync_transactions_pagination(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_transactions should handle pagination (has_more=True)."""
    # Create account
    account = Account(
        user_id=test_plaid_item_for_services.user_id,
        plaid_item_id=test_plaid_item_for_services.id,
        plaid_account_id="acc_page",
        name="Page Test",
        account_type="checking",
        provider="plaid",
        account_num="5555",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # Mock paginated responses
    response_page1 = {
        "added": [
            {
                "transaction_id": "tx_page_1",
                "account_id": "acc_page",
                "amount": 10.0,
                "date": "2025-01-01",
                "merchant_name": "Store 1",
                "name": "Store 1",
                "transaction_type": "debit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": True,
        "next_cursor": "cursor_page2"
    }
    
    response_page2 = {
        "added": [
            {
                "transaction_id": "tx_page_2",
                "account_id": "acc_page",
                "amount": 20.0,
                "date": "2025-01-02",
                "merchant_name": "Store 2",
                "name": "Store 2",
                "transaction_type": "debit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_final"
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.transactions_sync.side_effect = [response_page1, response_page2]
    
    result = sync_transactions(test_plaid_item_for_services.id, db_session)
    
    assert result["added"] == 2
    
    # Verify both transactions created
    assert db_session.query(Transaction).filter_by(plaid_transaction_id="tx_page_1").first() is not None
    assert db_session.query(Transaction).filter_by(plaid_transaction_id="tx_page_2").first() is not None
    
    # Verify final cursor saved
    db_session.refresh(test_plaid_item_for_services)
    assert test_plaid_item_for_services.transactions_cursor == "cursor_final"


def test_sync_transactions_modifies_existing(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_transactions should update modified transactions."""
    # Create account
    account = Account(
        user_id=test_plaid_item_for_services.user_id,
        plaid_item_id=test_plaid_item_for_services.id,
        plaid_account_id="acc_mod",
        name="Modify Test",
        account_type="checking",
        provider="plaid",
        account_num="6666",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # Create existing transaction
    existing_tx = Transaction(
        user_id=test_plaid_item_for_services.user_id,
        account_id=account.id,
        amount=Decimal("-50.00"),
        date=date(2025, 1, 1),
        description="Old Description",
        plaid_transaction_id="tx_mod_1",
        provider_tx_id="tx_mod_1",
        category_id=None,
        is_subscription=False
    )
    db_session.add(existing_tx)
    db_session.commit()
    original_id = existing_tx.id
    
    # Mock response with modified transaction
    mock_response = {
        "added": [],
        "modified": [
            {
                "transaction_id": "tx_mod_1",
                "account_id": "acc_mod",
                "amount": 75.00,
                "date": "2025-01-02",
                "merchant_name": "Updated Merchant",
                "name": "Updated Merchant",
                "transaction_type": "debit"
            }
        ],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_mod"
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.transactions_sync.return_value = mock_response
    
    result = sync_transactions(test_plaid_item_for_services.id, db_session)
    
    assert result["modified"] == 1
    
    # Verify transaction updated (same ID)
    updated_tx = db_session.query(Transaction).filter_by(id=original_id).first()
    assert updated_tx is not None
    assert updated_tx.amount == Decimal("-75.00")
    assert updated_tx.date == date(2025, 1, 2)
    assert updated_tx.description == "Updated Merchant"


def test_sync_transactions_removes_deleted(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_transactions should delete removed transactions."""
    # Create account
    account = Account(
        user_id=test_plaid_item_for_services.user_id,
        plaid_item_id=test_plaid_item_for_services.id,
        plaid_account_id="acc_del",
        name="Delete Test",
        account_type="checking",
        provider="plaid",
        account_num="7777",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # Create transaction to be deleted
    to_delete = Transaction(
        user_id=test_plaid_item_for_services.user_id,
        account_id=account.id,
        amount=Decimal("-100.00"),
        date=date(2025, 1, 1),
        description="To Be Deleted",
        plaid_transaction_id="tx_del_1",
        provider_tx_id="tx_del_1",
        category_id=None,
        is_subscription=False
    )
    db_session.add(to_delete)
    db_session.commit()
    
    # Mock response with removed transaction
    mock_response = {
        "added": [],
        "modified": [],
        "removed": ["tx_del_1"],
        "has_more": False,
        "next_cursor": "cursor_del"
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.transactions_sync.return_value = mock_response
    
    result = sync_transactions(test_plaid_item_for_services.id, db_session)
    
    assert result["removed"] == 1
    
    # Verify transaction deleted
    deleted_tx = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_del_1").first()
    assert deleted_tx is None


def test_sync_transactions_skips_duplicate(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_transactions should skip transactions that already exist."""
    # Create account
    account = Account(
        user_id=test_plaid_item_for_services.user_id,
        plaid_item_id=test_plaid_item_for_services.id,
        plaid_account_id="acc_dup",
        name="Duplicate Test",
        account_type="checking",
        provider="plaid",
        account_num="8888",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # Create existing transaction
    existing = Transaction(
        user_id=test_plaid_item_for_services.user_id,
        account_id=account.id,
        amount=Decimal("-30.00"),
        date=date(2025, 1, 1),
        description="Existing",
        plaid_transaction_id="tx_dup_1",
        provider_tx_id="tx_dup_1",
        category_id=None,
        is_subscription=False
    )
    db_session.add(existing)
    db_session.commit()
    
    # Mock response trying to add same transaction
    mock_response = {
        "added": [
            {
                "transaction_id": "tx_dup_1",  # Duplicate!
                "account_id": "acc_dup",
                "amount": 30.0,
                "date": "2025-01-01",
                "merchant_name": "Duplicate",
                "name": "Duplicate",
                "transaction_type": "debit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_dup"
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.transactions_sync.return_value = mock_response
    
    result = sync_transactions(test_plaid_item_for_services.id, db_session)
    
    # Should skip duplicate
    assert result["added"] == 0
    
    # Verify only one transaction exists
    all_txs = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_dup_1").all()
    assert len(all_txs) == 1


def test_sync_transactions_skips_unknown_account(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_transactions should skip transactions for accounts not in DB."""
    # Don't create any account
    
    mock_response = {
        "added": [
            {
                "transaction_id": "tx_unknown",
                "account_id": "acc_does_not_exist",  # No such account
                "amount": 99.0,
                "date": "2025-01-01",
                "merchant_name": "Unknown",
                "name": "Unknown",
                "transaction_type": "debit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_unknown"
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.transactions_sync.return_value = mock_response
    
    result = sync_transactions(test_plaid_item_for_services.id, db_session)
    
    # Should skip transaction
    assert result["added"] == 0
    
    # Verify no transaction created
    assert db_session.query(Transaction).count() == 0


def test_sync_transactions_handles_date_object(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_transactions should handle date objects (not just strings) from Plaid SDK."""
    # Create account
    account = Account(
        user_id=test_plaid_item_for_services.user_id,
        plaid_item_id=test_plaid_item_for_services.id,
        plaid_account_id="acc_date",
        name="Date Test",
        account_type="checking",
        provider="plaid",
        account_num="9999",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # Mock response with date object (not string)
    mock_response = {
        "added": [
            {
                "transaction_id": "tx_date_obj",
                "account_id": "acc_date",
                "amount": 15.0,
                "date": date(2025, 1, 10),  # date object, not string
                "merchant_name": "Date Object Test",
                "name": "Date Object Test",
                "transaction_type": "debit"
            }
        ],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_date"
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.transactions_sync.return_value = mock_response
    
    result = sync_transactions(test_plaid_item_for_services.id, db_session)
    
    assert result["added"] == 1
    
    # Verify transaction created with correct date
    tx = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_date_obj").first()
    assert tx is not None
    assert tx.date == date(2025, 1, 10)


def test_sync_transactions_uses_cursor(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_transactions should use stored cursor for incremental syncs."""
    # Set existing cursor
    test_plaid_item_for_services.transactions_cursor = "existing_cursor_abc"
    db_session.commit()
    
    # Create account
    account = Account(
        user_id=test_plaid_item_for_services.user_id,
        plaid_item_id=test_plaid_item_for_services.id,
        plaid_account_id="acc_cursor",
        name="Cursor Test",
        account_type="checking",
        provider="plaid",
        account_num="0001",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    mock_response = {
        "added": [],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "new_cursor_xyz"
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.transactions_sync.return_value = mock_response
    
    sync_transactions(test_plaid_item_for_services.id, db_session)
    
    # Verify cursor was passed to Plaid API
    call_args = mock_plaid_client.transactions_sync.call_args
    request = call_args[0][0]
    assert request.cursor == "existing_cursor_abc"
    
    # Verify cursor updated to new value
    db_session.refresh(test_plaid_item_for_services)
    assert test_plaid_item_for_services.transactions_cursor == "new_cursor_xyz"


def test_sync_transactions_handles_sdk_objects(db_session, test_plaid_item_for_services, mock_plaid_client):
    """sync_transactions should handle Plaid SDK object responses (with .to_dict() method)."""
    # Create account
    account = Account(
        user_id=test_plaid_item_for_services.user_id,
        plaid_item_id=test_plaid_item_for_services.id,
        plaid_account_id="acc_sdk_obj",
        name="SDK Object Test",
        account_type="checking",
        provider="plaid",
        account_num="1111",
        balance=Decimal("1000.00"),
        is_active=True
    )
    db_session.add(account)
    db_session.commit()
    
    # Mock Plaid SDK transaction object (has .to_dict() method)
    mock_tx_obj = MagicMock()
    mock_tx_obj.to_dict.return_value = {
        "transaction_id": "tx_sdk_obj",
        "account_id": "acc_sdk_obj",
        "amount": 25.50,
        "date": date(2025, 1, 15),
        "merchant_name": "SDK Object Store",
        "name": "SDK Object Store",
        "transaction_type": "debit"
    }
    
    # Mock response with SDK objects
    mock_response = {
        "added": [mock_tx_obj],  # SDK object, not dict
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "cursor_sdk"
    }
    
    # Configure the mock client from the fixture
    mock_plaid_client.transactions_sync.return_value = mock_response
    
    result = sync_transactions(test_plaid_item_for_services.id, db_session)
    
    assert result["added"] == 1
    
    # Verify transaction created
    tx = db_session.query(Transaction).filter_by(plaid_transaction_id="tx_sdk_obj").first()
    assert tx is not None
    assert tx.description == "SDK Object Store"
    assert tx.amount == Decimal("-25.50")  # Debit = negative
    assert tx.date == date(2025, 1, 15)
