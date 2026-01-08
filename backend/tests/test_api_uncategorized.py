from datetime import date
from decimal import Decimal

import pytest

from app.db.models import Account, Category, Transaction
from app.api.agents import routes as agents_routes

def test_process_uncategorized_empty(authed_client, mocker):
  bg_spy = mocker.patch("fastapi.BackgroundTasks.add_task", autospec=True)

  res = authed_client.post("/api/agents/process-uncategorized")
  assert res.status_code == 200
  assert res.json() == {"message": "Nothing to process"}

  bg_spy.assert_not_called()

def test_process_uncategorized_requires_auth(client):
  res = client.post("/api/agents/process-uncategorized")
  assert res.status_code in (401, 403)

def test_process_uncategorized_queues_ids_dont_run_real_bg(authed_client, db_session, mocker, test_user):
  """
  Tests:
  - endpoint queues process_batch_bg with correct transaction IDs
  - background task is called with the right function and args
  """

  bg_spy = mocker.patch("fastapi.BackgroundTasks.add_task", autospec=True)

  acct = Account (
    user_id = test_user.id,
    name="Checking", 
    account_type="checking",
    provider="Test",
    account_num="1234",
    balance=Decimal("0.00"),
    is_active=True,
  )
  db_session.add(acct)
  db_session.flush()

  tx = [Transaction(
    user_id = test_user.id,
    account_id = acct.id,
    amount = Decimal("-5.50"),
    date = date.today(),
    description = f"STARBUCKS #{i}",
    category_id = None,
  )
  for i in range(3)
  ]
  db_session.add_all(tx)
  db_session.commit()
  
  # Refresh to get IDs
  for t in tx:
    db_session.refresh(t)
  expected_ids = [t.id for t in tx]

  res = authed_client.post("/api/agents/process-uncategorized?limit=100")
  assert res.status_code == 200 
  assert res.json()["queued"] == 3

  # Verify the background task was called correctly
  bg_spy.assert_called_once()
  args, kwargs = bg_spy.call_args
  
  # args[0] is BackgroundTasks instance (self)
  # args[1] is the function to run
  # args[2] is the list of tx_ids
  assert args[1] is agents_routes.process_batch_bg  # Verify actual function object
  queued_ids = args[2]
  assert isinstance(queued_ids, list)
  assert len(queued_ids) == 3
  
  # Verify the queued IDs are exactly the ones we created
  assert set(queued_ids) == set(expected_ids)

def test_process_uncategorized_respects_limit(authed_client, db_session, mocker, test_user):
  """
  Tests:
  - limit parameter restricts how many transactions are queued
  """
  bg_spy = mocker.patch("fastapi.BackgroundTasks.add_task", autospec=True)

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

  # Create 5 uncategorized transactions
  tx = [Transaction(
    user_id=test_user.id,
    account_id=acct.id,
    amount=Decimal("-5.50"),
    date=date.today(),
    description=f"Transaction {i}",
    category_id=None,
  )
  for i in range(5)
  ]
  db_session.add_all(tx)
  db_session.commit()
  
  # Refresh to get IDs
  for t in tx:
    db_session.refresh(t)
  all_ids = [t.id for t in tx]

  # Request with limit=2
  res = authed_client.post("/api/agents/process-uncategorized?limit=2")
  assert res.status_code == 200
  assert res.json()["queued"] == 2  # Should only queue 2, not all 5

  # Verify only 2 IDs were queued, and they're from our created transactions
  bg_spy.assert_called_once()
  args, kwargs = bg_spy.call_args
  assert args[1] is agents_routes.process_batch_bg  # Correct function
  queued_ids = args[2]
  assert len(queued_ids) == 2  # Respects limit
  assert all(qid in all_ids for qid in queued_ids)  # IDs are from our transactions

def test_process_uncategorized_ignores_already_categorized(authed_client, db_session, mocker, test_user):
  bg_spy = mocker.patch("fastapi.BackgroundTasks.add_task", autospec=True)

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

  # 2 uncategorized
  uncategorized = [
    Transaction(
      user_id=test_user.id,
      account_id=acct.id,
      amount=Decimal("-5.50"),
      date=date.today(),
      description=f"Uncat {i}",
      category_id=None,
    )
    for i in range(2)
  ]

  # 1 categorized (should NOT be queued)
  categorized_cat = Category(name="Some Category")
  db_session.add(categorized_cat)
  db_session.flush()

  categorized = Transaction(
    user_id=test_user.id,
    account_id=acct.id,
    amount=Decimal("-7.25"),
    date=date.today(),
    description="Already categorized",
    category_id=categorized_cat.id,  # must exist due to FK constraint
  )

  db_session.add_all([*uncategorized, categorized])
  db_session.commit()

  for t in uncategorized:
    db_session.refresh(t)
  expected_ids = [t.id for t in uncategorized]

  res = authed_client.post("/api/agents/process-uncategorized?limit=100")
  assert res.status_code == 200
  assert res.json()["queued"] == 2

  bg_spy.assert_called_once()
  args, _ = bg_spy.call_args
  assert args[1] is agents_routes.process_batch_bg
  queued_ids = args[2]
  assert set(queued_ids) == set(expected_ids)