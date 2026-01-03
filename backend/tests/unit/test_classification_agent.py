import pytest
from sqlalchemy import select
from decimal import Decimal
from datetime import date

from app.db.models import Category, User, Account, Transaction
from app.agent.types import TransactionClassificationOutput
from app.agent.classification_agent import ClassificationAgent
from app.agent.cache import set_cached_categorization, get_cached_categorization  



def patch_llm(mocker):
  """Patch ClassificationAgent._call_llm so tests never hit the real LLM."""
  return mocker.patch(
      "app.agent.classification_agent.ClassificationAgent._call_llm",
      autospec=True,
      return_value=TransactionClassificationOutput(
          category_name="Other",
          is_subscription=False,
          tags=[],
      ),
  )


@pytest.fixture()
def seed_categories(db_session):
  """Insert the minimal categories required by ClassificationAgent (must include 'Other')."""
  cats = [Category(name="Dining"), Category(name="Subscriptions"), Category(name="Other")]
  for c in cats:
      db_session.add(c)
  db_session.commit()

  rows = db_session.execute(select(Category)).scalars().all()
  return {c.name: c.id for c in rows}


@pytest.fixture()
def seed_user_and_account(db_session):
  """Create a test user and account for categorization cache foreign key constraints."""
  user = User(
    email="test@example.com",
    name="Test User",
    password_hash="dummy_hash"
  )
  db_session.add(user)
  db_session.flush()  # Get user.id without committing
  
  account = Account(
    user_id=user.id,
    name="Test Account",
    account_type="checking",
    provider="test",
    account_num="123456",
    balance=Decimal("1000.00"),
    is_active=True
  )
  db_session.add(account)
  db_session.commit()
  db_session.refresh(user)
  db_session.refresh(account)
  return user.id, account.id


@pytest.fixture()
def user_id(seed_user_and_account):
  """Test user id from seeded user."""
  user_id, _ = seed_user_and_account
  return user_id

@pytest.fixture()
def account_id(seed_user_and_account):
  """Test account id from seeded account."""
  _, account_id = seed_user_and_account
  return account_id


class TestClassificationAgent:

  def test_rule_hit_returns_rule_source_and_does_not_call_llm(self, db_session, mocker, seed_categories, user_id):
    """Rule hit -> returns source='rule', does not call LLM, and caches the result."""
    llm = patch_llm(mocker)
    agent = ClassificationAgent(db_session)

    merchant = "Starbucks"
    cat_id, is_sub, tags, source = agent.categorize_transaction(
        user_id=user_id,
        merchant=merchant,
        amount=Decimal("-5.50"),
        description="STARBUCKS",
        transaction_date=date(2024, 1, 15),
    )

    assert source == "rule"
    assert cat_id == seed_categories["Dining"]
    assert is_sub is False
    assert "expense" in tags
    llm.assert_not_called()
    
    # Verify rule result was cached
    cached = get_cached_categorization(user_id, merchant, db_session)
    assert cached is not None
    assert cached.category_id == seed_categories["Dining"]
    assert cached.is_subscription is False
    assert "expense" in cached.tags

  def test_cache_hit_returns_cache_source_and_does_not_call_llm(self, db_session, mocker, seed_categories, user_id):
    """Cache hit -> returns source='cache' and does not call LLM."""
    llm = patch_llm(mocker)

    # Pre-seed cache for THIS merchant
    set_cached_categorization(
        user_id,
        "Some Merchant",
        seed_categories["Subscriptions"],
        True,
        ["expense", "recurring"],
        "agent_learning",
        db_session,
    )

    agent = ClassificationAgent(db_session)

    cat_id, is_sub, tags, source = agent.categorize_transaction(
        user_id=user_id,
        merchant="Some Merchant",
        amount=Decimal("-9.99"),
        description="SOME MERCHANT",
        transaction_date=date(2024, 1, 15),
    )

    assert source == "cache"
    assert cat_id == seed_categories["Subscriptions"]
    assert is_sub is True
    assert "expense" in tags
    assert "recurring" in tags
    llm.assert_not_called()

  def test_llm_hit_returns_llm_source_and_caches(self, db_session, mocker, seed_categories, user_id):
    """Rule/cache miss -> calls LLM once, returns source='llm', and writes cache."""
    llm = patch_llm(mocker)
    llm.return_value = TransactionClassificationOutput(
        category_name="Dining",
        is_subscription=False,
        tags=["expense"],
    )

    agent = ClassificationAgent(db_session)

    merchant = "Weird Merchant XYZ"  # should not match rule-based categorization
    cat_id, is_sub, tags, source = agent.categorize_transaction(
        user_id=user_id,
        merchant=merchant,
        amount=Decimal("-12.00"),
        description="WEIRD MERCHANT",
        transaction_date=date(2024, 1, 15),
    )

    assert source == "llm"
    assert cat_id == seed_categories["Dining"]
    assert is_sub is False
    assert tags == ["expense"]
    llm.assert_called_once()

    cached = get_cached_categorization(user_id, merchant, db_session)
    assert cached is not None
    assert cached.category_id == seed_categories["Dining"]

  def test_llm_invalid_category_name_falls_back_to_other(self, db_session, mocker, seed_categories, user_id):
    """If LLM returns an unknown category, validate_category_name forces 'Other'."""
    llm = patch_llm(mocker)
    llm.return_value = TransactionClassificationOutput(
        category_name="Invalid Category",
        is_subscription=False,
        tags=["expense"],
    )

    agent = ClassificationAgent(db_session)

    cat_id, is_sub, tags, source = agent.categorize_transaction(
        user_id=user_id,
        merchant="Unknown Merchant",
        amount=Decimal("-5.50"),
        description="UNKNOWN MERCHANT",
        transaction_date=date(2024, 1, 15),
    )

    assert source == "llm"
    assert cat_id == seed_categories["Other"]
    llm.assert_called_once()

  def test_llm_error_returns_fallback(self, db_session, mocker, seed_categories, user_id):
    """If LLM throws, agent returns (Other, False, [], 'fallback')."""
    llm = patch_llm(mocker)
    llm.side_effect = Exception("LLM down")

    agent = ClassificationAgent(db_session)

    cat_id, is_sub, tags, source = agent.categorize_transaction(
        user_id=user_id,
        merchant="Unknown Merchant",
        amount=Decimal("-5.50"),
        description="UNKNOWN MERCHANT",
        transaction_date=date(2024, 1, 15),
    )

    assert source == "fallback"
    assert cat_id == seed_categories["Other"]
    assert is_sub is False
    assert tags == []
    llm.assert_called_once()

  def test_pattern_detection_overrides_llm_subscription_flag(self, db_session, mocker, seed_categories, user_id, account_id):
    """If pattern detection says subscription=True, it overrides LLM is_subscription=False and caches it."""
    llm = patch_llm(mocker)
    llm.return_value = TransactionClassificationOutput(
        category_name="Other",
        is_subscription=False,
        tags=[],
    )

    agent = ClassificationAgent(db_session)

    # Create actual transaction records for pattern detection
    # This avoids mocking db.execute which breaks get_cached_categorization
    transactions = [
      Transaction(
        user_id=user_id,
        account_id=account_id,
        amount=Decimal("-9.99"),
        date=date(2024, 1, 15),
        description="RECURRING SERVICE",
        normalized_merchant="RECURRING SERVICE",
        category_id=seed_categories["Other"]
      ),
      Transaction(
        user_id=user_id,
        account_id=account_id,
        amount=Decimal("-9.99"),
        date=date(2024, 2, 15),
        description="RECURRING SERVICE",
        normalized_merchant="RECURRING SERVICE",
        category_id=seed_categories["Other"]
      ),
      Transaction(
        user_id=user_id,
        account_id=account_id,
        amount=Decimal("-9.99"),
        date=date(2024, 3, 15),
        description="RECURRING SERVICE",
        normalized_merchant="RECURRING SERVICE",
        category_id=seed_categories["Other"]
      ),
    ]
    for tx in transactions:
      db_session.add(tx)
    db_session.commit()

    # Use normalized merchant name to match the transactions in the database
    merchant = "RECURRING SERVICE"
    cat_id, is_sub, tags, source = agent.categorize_transaction(
        user_id=user_id,
        merchant=merchant,
        amount=Decimal("-9.99"),
        description="RECURRING SERVICE",
        transaction_date=date(2024, 4, 15),
    )

    assert source == "llm"
    assert is_sub is True
    llm.assert_called_once()
    
    # Verify the decision was cached with is_subscription=True
    cached = get_cached_categorization(user_id, merchant, db_session)
    assert cached is not None
    assert cached.is_subscription is True