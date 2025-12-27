""" Agent DB  writes """

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..db.models import Transaction

logger = logging.getLogger(__name__)

def get_transaction(transaction_id: int, db: Session) -> dict:
  """ Gets transaction data and returns dict with the transaction fields"""
  tx = db.execute(select(Transaction).where(Transaction.id == transaction_id)).scalar_one()
  return {
    "id": tx.id,
    "user_id": tx.user_id,
    "description":tx.description or "",
    "amount": tx.amount,
    "date": tx.date,
  }

def update_transaction(transaction_id: int, normalized_merchant: str, category_id: int, is_subscription: bool, tags: list[str], db: Session) -> None:
  """Update transaction w/ agent results"""
  tx = db.execute(select(Transaction).where(Transaction.id == transaction_id)).scalar_one()
  tx.normalized_merchant = normalized_merchant 
  tx.category_id = category_id 
  tx.is_subscription = is_subscription 
  tx.tags = tags
  db.commit()
  logger.info(f"Updated tx {transaction_id}")

  