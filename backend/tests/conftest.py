import os 
from dotenv import load_dotenv
import pytest
from sqlalchemy import create_engine, event, text 
from sqlalchemy.orm import sessionmaker 
from unittest.mock import MagicMock, patch

from app.db.base import Base

# --- FastAPI integration testing imports ---
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.db.session import get_db
from app.core.auth import get_current_user
from app.db.models import User

load_dotenv(".env.test")

# --- Global Plaid mock to prevent real API calls ---
@pytest.fixture(scope="function")
def mock_plaid_client():
    """Create a mock Plaid client with default return values.
    
    Tests can customize this mock by accessing the fixture and configuring
    the return values as needed.
    """
    mock_client = MagicMock()
    
    # Set default return values to prevent AttributeErrors
    mock_client.link_token_create.return_value = {"link_token": "mock-link-token"}
    mock_client.item_public_token_exchange.return_value = {
        "access_token": "mock-access-token",
        "item_id": "mock-item-id"
    }
    mock_client.accounts_get.return_value = {"accounts": []}
    mock_client.transactions_sync.return_value = {
        "added": [],
        "modified": [],
        "removed": [],
        "has_more": False,
        "next_cursor": "mock-cursor"
    }
    
    return mock_client


@pytest.fixture(autouse=True)
def force_plaid_mock(monkeypatch, mock_plaid_client):
    """
    Prevent ALL tests from ever creating a real Plaid client.
    
    This fixture runs automatically for every test (autouse=True).
    It patches get_plaid_client() where it's USED, not where it's defined.
    """
    # Reset the _client cache to None before each test
    import app.api.plaid.client as plaid_client_module
    plaid_client_module._client = None
    
    # Patch where get_plaid_client is USED (in services.py)
    monkeypatch.setattr(
        "app.api.plaid.services.get_plaid_client",
        lambda: mock_plaid_client
    )
    
    # Patch where get_plaid_client is USED (in routes.py)
    monkeypatch.setattr(
        "app.api.plaid.routes.get_plaid_client",
        lambda: mock_plaid_client
    )

TEST_DB_URL = os.getenv("TEST_DB_URL")

@pytest.fixture(scope="session")
def engine():
  if not TEST_DB_URL:
    raise RuntimeError(
      "TEST_DB_URL is not set"
    )
  
  engine = create_engine(TEST_DB_URL, future=True)

  # sanity check that the database is reachable
  with engine.connect() as conn:
    conn.execute(text("SELECT 1"))

  # create tables once per test session
  Base.metadata.create_all(bind=engine)
  yield engine 
  Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session(engine):
  """Provide a SQLAlchemy Session isolated per test using an outer transaction + SAVEPOINT.

  This keeps tests isolated even if application code calls session.commit().
  """
  # One connection + outer transaction per test 
  connection = engine.connect()
  transaction = connection.begin()

  SessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)
  session = SessionLocal()

  # Start a SAVEPOINT. When code commits, the SAVEPOINT ends; restart it automatically.
  session.begin_nested()

  def restart_savepoint(sess, trans):
    """Restart a savepoint after a transaction ends."""
    if trans.nested and not trans._parent.nested:
      sess.begin_nested()

  event.listen(session, "after_transaction_end", restart_savepoint)

  try:
    yield session
  finally:
    # Remove listener to avoid leaking handlers between tests
    try:
      event.remove(session, "after_transaction_end", restart_savepoint)
    except Exception:
      pass
    session.close()
    transaction.rollback()
    connection.close()


# --- FastAPI integration testing fixtures ---

@pytest.fixture()
def app(db_session):
  """FastAPI app with dependency overrides wired to the per-test db_session."""

  # Ensure clean slate (no leakage from other tests)
  fastapi_app.dependency_overrides.clear()

  def _override_get_db():
    yield db_session

  fastapi_app.dependency_overrides[get_db] = _override_get_db

  yield fastapi_app

  # Cleanup
  fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def client(app):
  """HTTP client for integration testing FastAPI routes."""
  return TestClient(app)


@pytest.fixture()
def test_user(db_session):
  """Create and return a real User row for endpoint tests."""
  user = User(email="test@example.com", name="Test User", password_hash="supabase_managed")
  db_session.add(user)
  db_session.commit()
  db_session.refresh(user)
  return user


@pytest.fixture()
def authed_client(app, client, test_user):
  """TestClient that bypasses JWT and injects a current_user for protected endpoints."""

  def _override_get_current_user():
    return test_user

  # Keep existing DB override from `app` fixture; just add auth override.
  app.dependency_overrides[get_current_user] = _override_get_current_user
  return client
