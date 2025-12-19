"""Ingestion Agent: Rule → Cache → LLM merchant normalization."""
import logging
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.config import get_settings
from .types import MerchantNormalizationOutput
from .rules import normalize_merchant_rule_based, clean_merchant_fallback
from .cache import get_cached_normalization, set_cached_normalization
from .prompts import MERCHANT_NORMALIZATION_PROMPT

logger = logging.getLogger(__name__)
settings = get_settings()

class IngestionAgent:
  def __init__(self, db: Session):
    self.db = db
    self.llm = ChatOpenAI(
      model=settings.openai_model,
      temperature=0.0,
      timeout=30,
    ).with_structured_output(MerchantNormalizationOutput)

  def normalize_merchant(self, raw_merchant: str) -> tuple[str,str]:
    if not raw_merchant or not raw_merchant.strip():
      return ("Unknown Merchant", "invalid_input")
    
    clean = raw_merchant.strip()

    # Rules
    if rule_result := normalize_merchant_rule_based(clean):
      set_cached_normalization(clean, rule_result, self.db)
      return (rule_result, "rule")

    # Cache
    if cached := get_cached_normalization(clean, self.db):
      return (cached.normalized_merchant, "cache")

    try:
      result = self._call_llm(clean)
      set_cached_normalization(clean, result.normalized_merchant, self.db)
      return (result.normalized_merchant, "llm")
    except Exception as e:
      logger.error(f"LLM normalization failed for '{clean}': {e}")
      # NOT caching fallback results
      return (clean_merchant_fallback(clean), "fallback")

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2,max=10))
  def _call_llm(self, raw_merchant: str) -> MerchantNormalizationOutput:
    return self.llm.invoke([
      {"role": "system", "content": MERCHANT_NORMALIZATION_PROMPT},
      {"role": "user", "content": f"Normalize: {raw_merchant}"}
    ])