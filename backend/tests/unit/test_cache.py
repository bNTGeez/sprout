from app.agent.cache import normalize_cache_key, validate_tags, get_cached_normalization, set_cached_normalization
from app.db.models import MerchantNormalizationCache
from sqlalchemy import select 

class TestNormalizeCacheKey:

  def test_strips_and_uppercases(self):
    """normalize_cache_key strips whitespace and uppercases the merchant key."""

    raw = " AmZn  "

    result = normalize_cache_key(raw)

    assert result == "AMZN"


class TestValidateTags:

  def test_leans_deduplicates_and_drops_invalid(self):
    """validate_tags trims whitespace, removes duplicates, drops invalid entries, and caps tag length."""

    raw_tags = [" expense ", "expense", "", None, 123, "recurring", "recurring", "x" * 200]

    result = validate_tags(raw_tags)

    assert result == ["expense", "recurring", "x" * 50]


class TestMerchantNormalizationCache:

  def test_get_cached_normalization_miss(self, db_session):
    """Cache miss returns None when no normalization entry exists."""

    cached = get_cached_normalization("Doesnt exist", db_session)

    assert cached is None 

  def test_set_cached_normalization_upserts(self, db_session):
    """set_cached_normalization upserts by updating the existing row instead of inserting duplicates."""

    set_cached_normalization("AMZN", "Amazon", db_session)
    set_cached_normalization("AMZN", "Amazon.com", db_session)

    cached = get_cached_normalization("AMZN", db_session)

    assert cached is not None 
    assert cached.normalized_merchant == "Amazon.com"

    entries = (
      db_session.execute(
        select(MerchantNormalizationCache).where(
          MerchantNormalizationCache.raw_merchant == normalize_cache_key("AMZN")
        )
      )
      .scalars()
      .all()
    )
    assert len(entries) == 1

  def test_get_cached_normalization_does_not_commit(self, db_session, mocker):
    """Read-only guarantee: get_cached_normalization must not call commit()."""

    set_cached_normalization("TEST", "Test", db_session)
    commit_spy = mocker.spy(db_session, "commit")

    get_cached_normalization("TEST", db_session)

    commit_spy.assert_not_called()

  def test_set_then_get_cached_normalization(self, db_session):
    """Writing a normalization then reading it returns the cached value using a normalized key."""

    set_cached_normalization("AMZN", "Amazon", db_session)

    cached = get_cached_normalization("amzn", db_session)

    assert cached is not None 
    assert cached.normalized_merchant == "Amazon"
