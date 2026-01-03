from app.agent.cache import get_cached_normalization, set_cached_normalization
from app.agent.ingestion_agent import IngestionAgent
from app.agent.types import MerchantNormalizationOutput

# --- Helpers ---

def patch_llm(mocker):
  """mock the LLM call in IngestionAgent"""

  return mocker.patch(
    "app.agent.ingestion_agent.IngestionAgent._call_llm",
    autospec=True,
    return_value=MerchantNormalizationOutput(normalized_merchant="Mocked Merchant")
  )

class TestIngestionAgent:

  def test_empty_string_returns_invalid_input(self, db_session, mocker):
    """Empty input -> invalid_input; no LLM call."""
    llm = patch_llm(mocker)
    agent = IngestionAgent(db_session)

    merchant, source = agent.normalize_merchant("")

    assert merchant == "Unknown Merchant"
    assert source == "invalid_input"
    llm.assert_not_called()

  def test_whitespace_only_returns_invalid_input(self, db_session, mocker):
    """Whitespace-only input -> invalid_input; no LLM call."""
    llm = patch_llm(mocker)
    agent = IngestionAgent(db_session)

    merchant, source = agent.normalize_merchant("     ")

    assert merchant == "Unknown Merchant"
    assert source == "invalid_input"
    llm.assert_not_called()
  
  def test_rule_hit_returns_rule_result(self, db_session, mocker):
    """Rule hit returns normalized merchant with source='rule'; no LLM call."""
    llm = patch_llm(mocker)
    agent = IngestionAgent(db_session)

    merchant, source = agent.normalize_merchant("STARBUCKS #12345")

    assert merchant == "Starbucks"
    assert source == "rule"
    llm.assert_not_called()

  def test_rule_hit_caches_result(self, db_session, mocker):
    """Rule hit writes the normalized merchant into the cache."""
    llm = patch_llm(mocker)
    agent = IngestionAgent(db_session)

    agent.normalize_merchant("STARBUCKS #12345")

    cached = get_cached_normalization("STARBUCKS #12345", db_session)

    assert cached is not None
    assert cached.normalized_merchant == "Starbucks"
    llm.assert_not_called()

  def test_cache_hit_returns_cached_result(self, db_session, mocker):
    """Cache hit returns cached merchant with source='cache'; no LLM call."""
    llm = patch_llm(mocker)
    set_cached_normalization("RANDOM COFFEE SHOP", "Random Coffee", db_session)
    agent = IngestionAgent(db_session)

    merchant, source = agent.normalize_merchant("random coffee shop")

    assert merchant == "Random Coffee"
    assert source == "cache"
    llm.assert_not_called()

  def test_llm_hit_returns_llm_result(self, db_session, mocker):
    """Rule/cache miss calls LLM once and caches the LLM result."""
    llm = patch_llm(mocker)
    llm.return_value = MerchantNormalizationOutput(normalized_merchant="Custom Coffee Shop")
    agent = IngestionAgent(db_session)

    merchant, source = agent.normalize_merchant("CSTM COFFEE #999")

    assert merchant == "Custom Coffee Shop"
    assert source == "llm"
    llm.assert_called_once()

    cached = get_cached_normalization("CSTM COFFEE #999", db_session)
    assert cached is not None
    assert cached.normalized_merchant == "Custom Coffee Shop"

  def test_llm_failure_returns_fallback(self, db_session, mocker):
    """LLM error -> fallback normalization; fallback must not be cached."""
    llm = patch_llm(mocker)
    llm.side_effect = Exception("LLM down")

    agent = IngestionAgent(db_session)
    merchant, source = agent.normalize_merchant("TST* COFFEE SHOP")

    assert merchant == "Coffee Shop"
    assert source == "fallback"
    cached = get_cached_normalization("TST* COFFEE SHOP", db_session)
    assert cached is None

  def test_rule_hit_not_diff_merchant(self, db_session, mocker):
    """Rule hit must not create unrelated cache entries for other merchants."""
    llm = patch_llm(mocker)
    agent = IngestionAgent(db_session)

    merchant, source = agent.normalize_merchant("STARBUCKS #12345")

    assert merchant == "Starbucks"
    assert source == "rule"
    llm.assert_not_called()

    cached = get_cached_normalization("AMZN", db_session)
    assert cached is None