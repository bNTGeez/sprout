import os 
from dotenv import load_dotenv
import pytest
from sqlalchemy import create_engine, event, text 
from sqlalchemy.orm import sessionmaker 

from app.db.base import Base 

load_dotenv(".env.test")

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


  @event.listens_for(session, "after_transaction_end")
  def restart_savepoint(sess, trans):
    """Restart a savepoint after a transaction ends."""
    if trans.nested and not trans._parent.nested:
      sess.begin_nested()

  try:
    yield session
  finally:
    session.close()
    transaction.rollback()
    connection.close()