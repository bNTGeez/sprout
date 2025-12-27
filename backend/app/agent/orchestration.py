import logging
import time
from sqlalchemy.orm import Session

from .ingestion_agent import IngestionAgent
from .classification_agent import ClassificationAgent
from .persistence import get_transaction, update_transaction

logger = logging.getLogger(__name__)

def process_transaction(transaction_id: int, db: Session) -> dict:

  start = time.time()
  try:
    # Get Transaction
    tx = get_transaction(transaction_id, db)

    # Normalize Merchant
    ingest_agent = IngestionAgent(db)
    merchant, ingest_source = ingest_agent.normalize_merchant(tx["description"])

    # Categorize
    class_agent = ClassificationAgent(db)
    cat_id, is_sub, tags, class_source = class_agent.categorize_transaction(
      tx["user_id"], merchant, tx["amount"], tx["description"], tx["date"]
    )

    # Persist
    update_transaction(transaction_id, merchant, cat_id, is_sub, tags, db)

    elapsed_ms = (time.time() - start) * 1000
    llm_used = (ingest_source == "llm" or class_source == "llm")

    logger.info(
      f"TX {transaction_id}: {merchant} → cat {cat_id} | "
      f"sources: {ingest_source}/{class_source} | "
      f"llm: {llm_used} | {elapsed_ms:.0f}ms"
    )

    return {
      "success": True, 
      "normalized_merchant": merchant, 
      "category_id": cat_id,
      "decision_sources": {"ingest": ingest_source, "classify": class_source},
      "llm_used": llm_used, 
      "time_ms": round(elapsed_ms, 2),
      "error": None
    }

  except Exception as e:
    logger.error(f"Tx {transaction_id} failed: {e}")
    return {
      "success": False,
      "error": str(e),
      "llm_used": False,
      "time_ms": round((time.time() - start) * 1000, 2)
    }

  
