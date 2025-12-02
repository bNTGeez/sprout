"""Pydantic models for request and response payloads.

Define shapes of data that your API sends and receives here (e.g. Budget,
Transaction, Goal), separate from the SQLAlchemy models in `db/models.py`.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
