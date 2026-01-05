from decimal import Decimal
from datetime import date 

import pytest 
from sqlalchemy import select

from app.agent.orchestration import process_transaction
from app.db.models import User, Account, Category, Transaction

@pytest.fixture()
def seed_tx_for_orchestration(db_session):
  """
    Why this fixture:
    - orchestration loads a Transaction from DB by id
    - so we need a real Transaction row with required FKs
    """

  user = User(email="test@example.com", name="Test User", password_hash="dummy_hash")
  db_session.add(user)
  db_session.flush()

  account = Account(user_id=user.id, name="Test Account", account_type="checking", provider="Test Bank", account_num="1234", balance=Decimal("1000.00"), is_active=True)
  db_session.add(account)
  db_session.flush()

  dining = Category(name="Dining", icon="🍽️", color="#FF5733")
  other = Category(name="Other", icon="❓", color="#999999")
  db_session.add_all([dining, other])
  db_session.flush()

  tx = Transaction(user_id=user.id, account_id=account.id, amount=Decimal("-5.50"), date=date(2024, 1, 15), description="", normalized_merchant=None, category_id=other.id, is_subscription=False, tags=[])

  db_session.add(tx)
  db_session.commit()
  db_session.refresh(tx)

  return {
    "tx_id": tx.id,
    "category_ids": {"Dining": dining.id, "Other": other.id},
  }

def test_process_transaction_success(db_session, mocker, seed_tx_for_orchestration):
  """
    What this tests:
    - orchestration wires ingestion -> classification -> persistence
    - we mock agents to avoid re-testing rule/LLM logic
    - DB row gets updated
    - response dict matches contract (success, sources, llm_used, time_ms, error)
  """

  tx_id = seed_tx_for_orchestration["tx_id"]
  dining_id = seed_tx_for_orchestration["category_ids"]["Dining"]

  # Patch the class methods before instances are created
  mocker.patch("app.agent.orchestration.IngestionAgent.normalize_merchant", return_value=("Starbucks", "rule"))
  mocker.patch("app.agent.orchestration.ClassificationAgent.categorize_transaction", return_value=(dining_id, False, ["expense"], "rule"))

  result = process_transaction(tx_id, db_session)

  assert result["success"] is True
  assert result["normalized_merchant"] == "Starbucks"
  assert result["category_id"] == dining_id
  assert result["decision_sources"] == {"ingest": "rule", "classify": "rule"}
  assert result["llm_used"] is False
  assert "time_ms" in result
  assert result["error"] is None

  # DB updated by persistence
  tx = db_session.execute(select(Transaction).where(Transaction.id == tx_id)).scalar_one()
  assert tx.normalized_merchant == "Starbucks"
  assert tx.category_id == dining_id
  assert tx.is_subscription is False
  assert tx.tags == ["expense"]

def test_process_transaction_failure(db_session):
  """
    What this tests:
    - any exception is caught
    - returns success=False with error string
    - llm_used is False
    """

  result = process_transaction(99999, db_session)
  assert result["success"] is False
  assert isinstance(result["error"], str)
  assert result["llm_used"] is False
  assert "time_ms" in result


# New test: llm_used True if any stage uses llm
def test_process_transaction_sets_llm_used_true_if_any_stage_uses_llm(db_session, mocker, seed_tx_for_orchestration):
  """If ingestion or classification source is 'llm', llm_used should be True."""

  tx_id = seed_tx_for_orchestration["tx_id"]
  dining_id = seed_tx_for_orchestration["category_ids"]["Dining"]

  mocker.patch("app.agent.orchestration.IngestionAgent.normalize_merchant", return_value=("Starbucks", "llm"))
  mocker.patch("app.agent.orchestration.ClassificationAgent.categorize_transaction", return_value=(dining_id, False, ["expense"], "rule"))

  result = process_transaction(tx_id, db_session)

  assert result["success"] is True
  assert result["llm_used"] is True