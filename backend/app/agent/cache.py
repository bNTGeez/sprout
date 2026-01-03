import logging
from typing import Optional 
from sqlalchemy import select
from sqlalchemy.orm import Session 

from ..db.models import MerchantNormalizationCache, UserCategorizationCache
from .types import CachedMerchantNormalization, CachedCategorization

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
    Uses database-agnostic upsert (query then insert/update)
    Inserts if new, updates if exists
    Commits the transaction
  """

  cache_key = normalize_cache_key(raw_merchant)
  try:
      # Try to get existing record
      existing = db.execute(
          select(MerchantNormalizationCache).where(
              MerchantNormalizationCache.raw_merchant == cache_key
          )
      ).scalar_one_or_none()
      
      if existing:
          # Update existing record
          existing.normalized_merchant = normalized_merchant
          # updated_at will be set automatically by SQLAlchemy's onupdate
      else:
          # Insert new record
          new_cache = MerchantNormalizationCache(
              raw_merchant=cache_key,
              normalized_merchant=normalized_merchant
          )
          db.add(new_cache)
      
      db.commit()
      logger.debug(f"Cached normalization: '{raw_merchant}' → '{normalized_merchant}'")
  except Exception:
      db.rollback()
      logger.exception(f"Failed to cache normalization for '{raw_merchant}'")


# User Categorization Cache

def get_cached_categorization(user_id: int, merchant: str, db: Session) -> Optional[CachedCategorization]:
  """Look up a cached categorization for a user and merchant.
  
  Normalizes the merchant name to a cache key (uppercase).
  Returns CachedCategorization if found, None otherwise.
  Read-only (no commit)
  """
  # Note: normalized_merchant in DB is actually a cache key (uppercase), not a human-readable name
  merchant_key = normalize_cache_key(merchant)
  
  result = db.execute(
    select(UserCategorizationCache).where(
      UserCategorizationCache.user_id == user_id,
      UserCategorizationCache.normalized_merchant == merchant_key
    )
  ).scalar_one_or_none()
  
  if result:
    logger.debug(f"Cache HIT: categorization for user {user_id}, merchant '{merchant}'")
    return CachedCategorization(
      user_id=result.user_id,
      normalized_merchant=result.normalized_merchant,
      category_id=result.category_id,
      is_subscription=result.is_subscription,
      tags=result.tags or [],
      cached_at=result.created_at,
      source=result.source
    )
  
  logger.debug(f"Cache MISS: categorization for user {user_id}, merchant '{merchant}'")
  return None

def set_cached_categorization(
  user_id: int,
  merchant: str,
  category_id: int,
  is_subscription: bool,
  tags: list[str] | None,
  source: str,
  db: Session
) -> None:
  """Store a user categorization in the cache.
  
  Normalizes the merchant name to a cache key (uppercase).
  Validates tags.
  Uses database-agnostic upsert (query then insert/update).
  Inserts if new, updates if exists.
  Commits the transaction.
  """
  # Note: normalized_merchant in DB is actually a cache key (uppercase), not a human-readable name
  merchant_key = normalize_cache_key(merchant)
  validated_tags = validate_tags(tags)
  
  try:
    # Try to get existing record
    existing = db.execute(
      select(UserCategorizationCache).where(
        UserCategorizationCache.user_id == user_id,
        UserCategorizationCache.normalized_merchant == merchant_key
      )
    ).scalar_one_or_none()
    
    if existing:
      # Update existing record
      existing.category_id = category_id
      existing.is_subscription = is_subscription
      existing.tags = validated_tags if validated_tags else None
      existing.source = source
      # updated_at will be set automatically by SQLAlchemy's onupdate
    else:
      # Insert new record
      new_cache = UserCategorizationCache(
        user_id=user_id,
        normalized_merchant=merchant_key,
        category_id=category_id,
        is_subscription=is_subscription,
        tags=validated_tags if validated_tags else None,
        source=source
      )
      db.add(new_cache)
    
    db.commit()
    logger.debug(f"Cached categorization: user {user_id}, merchant '{merchant}' → category {category_id}, source '{source}'")
  except Exception:
    db.rollback()
    logger.exception(f"Failed to cache categorization for user {user_id}, merchant '{merchant}'")


