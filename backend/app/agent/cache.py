import logging
from typing import Optional 
from sqlalchemy import select, text
from sqlalchemy.orm import Session 
from sqlalchemy.exc import IntegrityError

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

# User Categorization Cache 

def get_cached_categorization(user_id: int, normalized_merchant: str, db: Session) -> Optional[CachedCategorization]:
  """ Look up how a user categorizes a merchant.
      Normalizes the merchant key
      Checks user_feedback first (user's manual correction)
      Falls back to agent_learning (agent's suggestion)
      Returns CachedCategorization if found, None otherwise
      Read-only (no commit)
  """

  cache_key = normalize_cache_key(normalized_merchant)
  query_feedback = select(UserCategorizationCache).where(
    UserCategorizationCache.user_id == user_id,
    UserCategorizationCache.normalized_merchant == cache_key,
    UserCategorizationCache.source == "user_feedback"
  )
  result = db.execute(query_feedback).scalar_one_or_none()

  # Fallback to agent_learning
  if not result:
    query_agent = select(UserCategorizationCache).where(
      UserCategorizationCache.user_id == user_id,
      UserCategorizationCache.normalized_merchant == cache_key,
      UserCategorizationCache.source == "agent_learning"
    )
    result = db.execute(query_agent).scalar_one_or_none()

  if result: 
    entry = result
    logger.debug(
      f"Cache HIT: categorization user={user_id}, merchant='{normalized_merchant}' "
      f"→ category_id={entry.category_id} (source: {entry.source})"
  )

    return CachedCategorization(
        user_id=entry.user_id,
        normalized_merchant=entry.normalized_merchant,
        category_id=entry.category_id,
        is_subscription=entry.is_subscription,
        tags=validate_tags(entry.tags),
        cached_at=entry.created_at,
        source=entry.source
    )

  logger.debug(f"Cache MISS: categorization user={user_id}, merchant='{normalized_merchant}'")
  return None

def set_cached_categorization(user_id: int, normalized_merchant: str, category_id: int, is_subscription: bool, tags: list[str], source: str, db: Session) -> None:
  """ Normalizes the merchant key
      Validates tags
      Checks if user_feedback already exists
      Skips write if trying to overwrite user_feedback with agent_learning
      Uses raw SQL upsert with CASE logic to protect user feedback
      Commits the transaction
  """

  cache_key = normalize_cache_key(normalized_merchant)
  validated_tags = validate_tags(tags)

  # Check existing entry
  existing = db.execute(
    select(UserCategorizationCache).where(
        UserCategorizationCache.user_id == user_id,
        UserCategorizationCache.normalized_merchant == cache_key
    )
  ).scalar_one_or_none()

  # NON-NEGOTIABLE: agent_learning cannot overwrite user_feedback
  if existing and existing.source == "user_feedback" and source == "agent_learning":
    logger.debug(
        f"Skipping cache write: user_feedback exists for user={user_id}, "
        f"merchant='{normalized_merchant}'"
    )
    return

  # Upsert using raw SQL (handles concurrency)
  try:
    stmt = text("""
        INSERT INTO user_categorization_cache
            (user_id, normalized_merchant, category_id, is_subscription, tags, source, created_at, updated_at)
        VALUES
            (:user_id, :merchant, :category_id, :is_sub, CAST(:tags AS jsonb), :source, NOW(), NOW())
        ON CONFLICT (user_id, normalized_merchant)
        DO UPDATE SET
            category_id = CASE
                WHEN user_categorization_cache.source = 'user_feedback' AND EXCLUDED.source = 'agent_learning'
                THEN user_categorization_cache.category_id
                ELSE EXCLUDED.category_id
            END,
            is_subscription = CASE
                WHEN user_categorization_cache.source = 'user_feedback' AND EXCLUDED.source = 'agent_learning'
                THEN user_categorization_cache.is_subscription
                ELSE EXCLUDED.is_subscription
            END,
            tags = CASE
                WHEN user_categorization_cache.source = 'user_feedback' AND EXCLUDED.source = 'agent_learning'
                THEN user_categorization_cache.tags
                ELSE EXCLUDED.tags
            END,
            source = CASE
                WHEN user_categorization_cache.source = 'user_feedback' AND EXCLUDED.source = 'agent_learning'
                THEN user_categorization_cache.source
                ELSE EXCLUDED.source
            END,
            updated_at = NOW()
    """)

    import json
    db.execute(stmt, {
        "user_id": user_id,
        "merchant": cache_key,
        "category_id": category_id,
        "is_sub": is_subscription,
        "tags": json.dumps(validated_tags),
        "source": source
    })
    db.commit()
    logger.debug(
        f"Cached categorization: user={user_id}, merchant='{normalized_merchant}' "
        f"→ category_id={category_id} (source: {source})"
    )
  except Exception as e:
      db.rollback()
      logger.warning(f"Failed to cache categorization: {e}")


def invalidate_user_cache(user_id: int, db: Session) -> int:
  """
  Purpose: Clear all cached categorizations for a user (reset).
  What it does:
  Finds all cache entries for the user
  Deletes them
  Commits
  Returns the count deleted
  When to use: User wants to reset their learned patterns and start fresh.
  """

  result = db.execute(
    select(UserCategorizationCache).where(
        UserCategorizationCache.user_id == user_id
    )
  )
  entries = result.scalars().all()
  count = len(entries)

  for entry in entries:
    db.delete(entry)

  db.commit()
  logger.info(f"Invalidated {count} cache entries for user {user_id}")
  return count





