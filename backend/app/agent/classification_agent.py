import logging
from decimal import Decimal 
from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI

from ..db.models import Category, Transaction
from ..core.config import get_settings
from .types import TransactionClassificationOutput
from .rules import categorize_transaction_rule_based, validate_category_name, detect_subscription_pattern
from .cache import get_cached_categorization, set_cached_categorization
from .prompts import get_classification_prompt
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
settings = get_settings()

class ClassificationAgent: 
  """This categorizes transactions."""

  def __init__(self, db: Session):
    self.db = db 
    categories = db.execute(select(Category)).scalars().all()
    self.category_map = {c.name: c.id for c in categories}
    self.category_names = list(self.category_map.keys())

    self.llm = ChatOpenAI(
      model=settings.openai_model,
      temperature=0.0,
      timeout=30,
    ).with_structured_output(TransactionClassificationOutput)

  def categorize_transaction(self, user_id: int, merchant: str, amount: Decimal, description: str, transaction_date: date) -> tuple[int, bool, list[str], str]:
    """Returns: (category_id, is_subscription, tags, decision_source)"""

    if rule_result := categorize_transaction_rule_based(merchant, float(amount)):
      cat_name, is_sub, tags = rule_result 
      cat_id = self.category_map.get(cat_name, self.category_map["Other"])
      set_cached_categorization(user_id, merchant, cat_id, is_sub, tags, "agent_learning", self.db)
      return (cat_id, is_sub, tags, "rule")

    if cached := get_cached_categorization(user_id, merchant, self.db):
      return (cached.category_id, cached.is_subscription, cached.tags or [], "cache")

    is_pattern_sub = False
    try:
      recent = self.db.execute(
        select(Transaction.amount, Transaction.date)
        .where(Transaction.user_id == user_id, Transaction.normalized_merchant == merchant)
        .order_by(Transaction.date.desc()).limit(5)
      ).all()
      if len(recent) >= 2:
        amounts = [float(tx[0]) for tx in recent]
        dates = [tx[1].isoformat() for tx in recent]
        is_pattern_sub = detect_subscription_pattern(amounts, dates)
    except Exception as e:
      logger.debug(f"Pattern detection skipped: {e}")

    try:
      result = self._call_llm(merchant, amount, description, transaction_date)

      valid_cat = validate_category_name(result.category_name, self.category_names)
      cat_id = self.category_map[valid_cat]
      is_sub = is_pattern_sub or result.is_subscription 

      set_cached_categorization(user_id, merchant, cat_id, is_sub, result.tags, "agent_learning", self.db)
      return (cat_id, is_sub, result.tags, "llm")

    except Exception as e:
      logger.error(f"LLM categorization failed for '{merchant}': {e}")
      return (self.category_map["Other"], False, [], "fallback")

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
  def _call_llm(self, merchant, amount, description, date) -> TransactionClassificationOutput:
    """ LLM call with retry """
    prompt = get_classification_prompt(self.category_names)
    return self.llm.invoke([
      {"role": "system", "content": prompt},
      {"role": "user", "content": f"Merchant: {merchant} \nAmount: ${amount:.2f}\nDate: {date}"}
    ])