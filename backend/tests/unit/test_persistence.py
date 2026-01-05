from decimal import Decimal
from datetime import date

import pytest
from sqlalchemy import select

from app.agent.persistence import get_transaction, update_transaction
from app.db.models import User, Account, Category, Transaction

@pytest.fixture()
def seed_user_and_account_category_tx(db_session):
  """
    Why this fixture:
    - persistence.py reads/writes Transaction rows
    - Transaction usually has FK requirements (user_id, account_id, category_id)
    - So we create the minimum valid graph: User -> Account, Categories, then Transaction.
  """
  user = User(email="test@example.com", name="Test User", password_hash="dummy_hash")
  db_session.add(user)
  db_session.flush() # get user.id without committing
  
  account = Account(user_id=user.id, name="Test Account", account_type="checking", provider="Test Bank", account_num="1234", balance=Decimal("1000.00"), is_active=True)
  db_session.add(account)
  db_session.flush()
  
  other = Category(name="Other", icon="❓", color="#999999")
  dining = Category(name="Dining", icon="🍽️", color="#FF5733")
  db_session.add_all([other, dining])
  db_session.flush()
  
  tx = Transaction(user_id=user.id, account_id=account.id, amount=Decimal("-5.50"), date=date(2024, 1, 15), description="", normalized_merchant=None, category_id=other.id, is_subscription=False, tags=[])
  db_session.add(tx)
  db_session.commit()
  db_session.refresh(tx)
  return {
    "user_id": user.id,
    "account_id": account.id,
    "category_id": {"Other": other.id, "Dining": dining.id},
    "tx_id": tx.id,
  }


class TestGetTransaction:
  
  def test_get_transaction_returns_expected_keys_and_default_description(self, db_session, seed_user_and_account_category_tx):
    """Test that get_transaction returns expected keys and default description when description is None."""
    tx_id = seed_user_and_account_category_tx["tx_id"]
    
    result = get_transaction(tx_id, db_session)
    
    assert "id" in result
    assert "user_id" in result
    assert "description" in result
    assert "amount" in result
    assert "date" in result
    assert result["description"] == ""  # Should default to "" when DB has NULL
    assert result["id"] == tx_id
    assert result["user_id"] == seed_user_and_account_category_tx["user_id"]
    assert result["amount"] == Decimal("-5.50")
  
  def test_get_transaction_returns_actual_description_when_set(self, db_session, seed_user_and_account_category_tx):
    """Test that get_transaction returns actual description when it's not None."""
    tx_id = seed_user_and_account_category_tx["tx_id"]
    
    # Update the transaction to have a description
    tx = db_session.execute(select(Transaction).where(Transaction.id == tx_id)).scalar_one()
    tx.description = "STARBUCKS #12345"
    db_session.commit()
    
    result = get_transaction(tx_id, db_session)
    
    assert result["description"] == "STARBUCKS #12345"


class TestUpdateTransaction:
  
  def test_update_transaction_writes_fields_and_commits(self, db_session, seed_user_and_account_category_tx):
    """Test that update_transaction writes all fields and commits."""
    tx_id = seed_user_and_account_category_tx["tx_id"]
    dining_id = seed_user_and_account_category_tx["category_id"]["Dining"]
    
    update_transaction(
      transaction_id=tx_id,
      normalized_merchant="Starbucks",
      category_id=dining_id,
      is_subscription=False,
      tags=["expense"],
      db=db_session,
    )
    
    # Re-query the transaction and assert values
    tx = db_session.execute(select(Transaction).where(Transaction.id == tx_id)).scalar_one()
    
    assert tx.normalized_merchant == "Starbucks"
    assert tx.category_id == dining_id
    assert tx.is_subscription is False
    assert tx.tags == ["expense"]
  
  def test_update_transaction_sets_subscription_and_tags(self, db_session, seed_user_and_account_category_tx):
    """Test that update_transaction correctly sets is_subscription and tags."""
    tx_id = seed_user_and_account_category_tx["tx_id"]
    dining_id = seed_user_and_account_category_tx["category_id"]["Dining"]
    
    update_transaction(
      transaction_id=tx_id,
      normalized_merchant="Netflix",
      category_id=dining_id,
      is_subscription=True,
      tags=["expense", "recurring"],
      db=db_session,
    )
    
    tx = db_session.execute(select(Transaction).where(Transaction.id == tx_id)).scalar_one()
    
    assert tx.normalized_merchant == "Netflix"
    assert tx.is_subscription is True
    assert tx.tags == ["expense", "recurring"]