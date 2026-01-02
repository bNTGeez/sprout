import logging
from typing import Optional 
from sqlalchemy import select, text
from sqlalchemy.orm import Session 
from sqlalchemy.exc import IntegrityError 

from ..db.models import MerchantNormalizationCache
from .types import CachedMerchantNormalization

logger = logging.getLogger(__name__)

def normalize_cache_key(merchant: str) -> str:
  """Normalize merchant strings for consistent cache lookups.
    Strips whitespace and converts to uppercase
  """

  return merchant.strip().upper()

def validate_tags(tags: list[str] | None) -> list[str]:
  """Ensure tags are valid: list of strings, deduped, limited length.

    Args:
        tags: Raw tags list

    Returns:
        Validated tags list
  """
  if not tags:
      return []

  # Validate type, strip, dedupe, limit
  validated = []
  seen = set()
  for tag in tags[:20]:  # Max 20 tags
      if isinstance(tag, str):
          clean = tag.strip()[:50]  # Max 50 chars per tag
          if clean and clean not in seen:
              validated.append(clean)
              seen.add(clean)

  return validated

# Merchant Normalization Cache 

def get_cached_normalization(raw_merchant: str, db: Session) -> Optional[CachedMerchantNormalization]:
  """ Look up a cached normalized merchant name 
      Normalizes the input key
      Queries merchant_normalization_cache table
      Returns CachedMerchantNormalization if found, None otherwise
      Read-only (no commit)
  """
  cache_key = normalize_cache_key(raw_merchant)
  query = select(MerchantNormalizationCache).where(MerchantNormalizationCache.raw_merchant == cache_key)
  result = db.execute(query).scalar_one_or_none()
  if result:
    logger.debug(f"Cache HIT: normalization '{raw_merchant}' → '{result.normalized_merchant}'")
    return CachedMerchantNormalization(
        raw_merchant=result.raw_merchant,
        normalized_merchant=result.normalized_merchant,
        cached_at=result.created_at
    )
  logger.debug(f"Cache MISS: normalization '{raw_merchant}'")
  return None

def set_cached_normalization(raw_merchant: str, normalized_merchant: str, db: Session) -> None: 
  """Store a merchant normalization in the cache.
    Normalizes the key
    Uses PostgreSQL ON CONFLICT DO UPDATE (upsert)
    Inserts if new, updates if exists
    Commits the transaction
  """

  cache_key = normalize_cache_key(raw_merchant)
  # Postgres upsert: ON CONFLICT DO UPDATE
  try:
      stmt = text("""
          INSERT INTO merchant_normalization_cache (raw_merchant, normalized_merchant, created_at, updated_at)
          VALUES (:raw, :normalized, NOW(), NOW())
          ON CONFLICT (raw_merchant)
          DO UPDATE SET
              normalized_merchant = EXCLUDED.normalized_merchant,
              updated_at = NOW()
      """)
      db.execute(stmt, {"raw": cache_key, "normalized": normalized_merchant})
      db.commit()
      logger.debug(f"Cached normalization: '{raw_merchant}' → '{normalized_merchant}'")
  except Exception as e:
      db.rollback()
      logger.warning(f"Failed to cache normalization: {e}")






