from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel

# Ingestion Agent
class MerchantNormalizationOutput(BaseModel):
    """LLM output for merchant normalization."""
    normalized_merchant: str

# Classification Agent
class TransactionClassificationOutput(BaseModel):
    """LLM output for transaction categorization."""
    category_name: str
    is_subscription: bool = False
    tags: list[str] = []

# Cache Results
class CachedMerchantNormalization(BaseModel):
    """Result from merchant normalization cache lookup."""
    raw_merchant: str
    normalized_merchant: str
    cached_at: datetime

class CachedCategorization(BaseModel):
    """Result from user categorization cache lookup."""
    user_id: int
    normalized_merchant: str
    category_id: int
    is_subscription: bool
    tags: list[str]
    cached_at: datetime
    source: str  # "user_feedback" or "agent_learning"