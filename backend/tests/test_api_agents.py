from datetime import date 
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.models import User, Account, Transaction

def test_process_transaction_requires_auth(client):
  """Protected endpoint should reject requests without auth."""
  res = client.post("/api/agents/process-transaction/1")
  assert res.status_code in (401, 403)

def test_process_transaction_404_missing(authed_client):
  """
  Tests:
  - endpoint returns 404 for nonexistent transaction
  """
  res = authed_client.post("/api/agents/process-transaction/999999")
  assert res.status_code == 404
  assert "not found" in res.json()["detail"].lower()

def test_process_transaction_404_other_user(authed_client, db_session, test_user):
  """
  Tests:
  - endpoint returns 404 for other user's transaction
  """
  other_user = User(email="other@example.com", name="Other User", password_hash="dummy_hash")
  db_session.add(other_user)
  db_session.flush()
  acct = Account(
    user_id = other_user.id,
    name = "Other Account",
    account_type = "checking",
    provider = "Test",
    account_num = "1234",
    balance = Decimal("0.00"),
    is_active = True,
  )
  db_session.add(acct)
  db_session.flush()

  tx = Transaction(
    user_id = other_user.id,
    account_id = acct.id,
    amount = Decimal("-10.00"),
    date = date.today(),
    description = "Other user transaction",
    category_id = None,
  )
  db_session.add(tx)
  db_session.commit()

  res = authed_client.post(f"/api/agents/process-transaction/{tx.id}")
  assert res.status_code == 404
  assert "not found" in res.json()["detail"].lower()

def test_process_transaction_success(authed_client, db_session, mocker, test_user):
  """Tests:
  - endpoint returns 200 for a transaction owned by the authed user
  - endpoint calls the orchestration layer (patched)
  - response shape matches the orchestration contract (don’t assert exact time_ms)
  """

  # Create the minimum DB state required for the route-level ownership check.
  acct = Account(
    user_id=test_user.id,
    name="Checking",
    account_type="checking",
    provider="Test",
    account_num="1234",
    balance=Decimal("0.00"),
    is_active=True,
  )
  db_session.add(acct)
  db_session.flush()  # we need acct.id for the Transaction FK

  tx = Transaction(
    user_id=test_user.id,
    account_id=acct.id,
    amount=Decimal("-5.50"),
    date=date.today(),
    description="STARBUCKS #12345",
    category_id=None,
  )
  db_session.add(tx)
  db_session.commit()
  db_session.refresh(tx)

  expected_cat_id = 123  # arbitrary; this test is about the route wiring, not categorization
  expected = {
    "success": True,
    "normalized_merchant": "Starbucks",
    "category_id": expected_cat_id,
    "decision_sources": {"ingest": "rule", "classify": "rule"},
    "llm_used": False,
    "time_ms": 12.3,  # arbitrary
    "error": None,
  }

  # IMPORTANT: the route imports process_transaction from app.agent.orchestration
  # inside the handler, so patch the orchestration module.
  spy = mocker.patch("app.agent.orchestration.process_transaction", return_value=expected)

  res = authed_client.post(f"/api/agents/process-transaction/{tx.id}")
  assert res.status_code == 200

  # Verify endpoint passes correct args to orchestration
  spy.assert_called_once()
  args, kwargs = spy.call_args
  assert args[0] == tx.id  # transaction_id
  assert isinstance(args[1], Session)  # db session from dependency (don't assert identity)

  data = res.json()
  assert set(data.keys()) == {
    "success",
    "normalized_merchant",
    "category_id",
    "decision_sources",
    "llm_used",
    "time_ms",
    "error",
  }
  assert data["success"] is True
  assert data["normalized_merchant"] == "Starbucks"
  assert data["category_id"] == expected_cat_id
  assert data["decision_sources"] == {"ingest": "rule", "classify": "rule"}
  assert data["llm_used"] is False
  assert data["error"] is None
  assert "time_ms" in data
  assert isinstance(data["time_ms"], (int, float))

def test_process_transaction_orchestration_error(authed_client, db_session, mocker, test_user):
  """Tests:
  - endpoint returns error response when orchestration fails
  - matches real orchestration failure contract
  """
  acct = Account(
    user_id=test_user.id,
    name="Checking",
    account_type="checking",
    provider="Test",
    account_num="1234",
    balance=Decimal("0.00"),
    is_active=True,
  )
  db_session.add(acct)
  db_session.flush()

  tx = Transaction(
    user_id=test_user.id,
    account_id=acct.id,
    amount=Decimal("-5.50"),
    date=date.today(),
    description="STARBUCKS #12345",
    category_id=None,
  )
  db_session.add(tx)
  db_session.commit()
  db_session.refresh(tx)

  # Real orchestration failure shape: no normalized_merchant, category_id, or decision_sources
  error_response = {
    "success": False,
    "error": "Failed to process transaction",
    "llm_used": False,
    "time_ms": 5.0,
  }

  mocker.patch("app.agent.orchestration.process_transaction", return_value=error_response)

  res = authed_client.post(f"/api/agents/process-transaction/{tx.id}")
  assert res.status_code == 200  # Still 200, but success=False in body
  
  data = res.json()
  assert set(data.keys()) == {"success", "error", "llm_used", "time_ms"}
  assert data["success"] is False
  assert data["error"] == "Failed to process transaction"
  assert data["llm_used"] is False
  assert isinstance(data["time_ms"], (int, float))