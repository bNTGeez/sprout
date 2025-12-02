"""Shared FastAPI dependency aliases.

Import from this module inside your route functions to get typed helpers like
`DbSession` and `get_db` instead of wiring SQLAlchemy directly every time.
"""

from sqlalchemy.orm import Session

from .db.session import get_db

DbSession = Session

__all__ = ["DbSession", "get_db"]
