import logging 
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy import select 
from sqlalchemy.orm import Session 

from ...db.session import get_db, SessionLocal
from ...db.models import Transaction
from ...core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

def process_batch_bg(transaction_ids: list[int]):
  """Background task: Creates fresh DB Session 
     Uses batch optimization: agents created once and not per transaction
  """

  from ...agent.ingestion_agent import IngestionAgent
  from ...agent.classification_agent import ClassificationAgent
  from ...agent.persistence import get_transaction, update_transaction

  db = SessionLocal()

  try:
    ingest_agent = IngestionAgent(db)
    class_agent = ClassificationAgent(db)

    for tx_id in transaction_ids:
      try:
        tx = get_transaction(tx_id, db)

        merchant, _ = ingest_agent.normalize_merchant(tx["description"])
        cat_id, is_sub, tags, _ = class_agent.categorize_transaction(
          tx["user_id"], merchant, tx["amount"], tx["description"], tx["date"]
        )

        update_transaction(tx_id, merchant, cat_id, is_sub, tags, db)
      except Exception as e:
        logger.error(f"TX {tx_id} failed: {e}")
  finally:
    db.close()

@router.post("/process-transaction/{transaction_id}")
def process_single(transaction_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
  """Process a single transaction through the agent workflow."""
  
  from ...agent.orchestration import process_transaction
  
  tx = db.execute(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == user.id)).scalar_one_or_none()
  if not tx:
    raise HTTPException(status_code=404, detail="Transaction not found")

  result = process_transaction(transaction_id, db)
  return result

@router.post("/process-uncategorized")
def process_uncategorized(background_tasks: BackgroundTasks, user=Depends(get_current_user), db: Session = Depends(get_db), limit: int = 100):
  """Process all uncategorize transactions"""
  tx_ids = list(db.execute(select(Transaction.id).where(Transaction.user_id == user.id, Transaction.category_id.is_(None)).limit(limit)).scalars())
  if not tx_ids:
    return {"message": "Nothing to process"}
  
  background_tasks.add_task(process_batch_bg, tx_ids)
  return {"queued": len(tx_ids)}

