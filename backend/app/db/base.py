"""Shared SQLAlchemy base class for all ORM models.

Every model in `db/models.py` should inherit from `Base` so SQLAlchemy can
discover your tables and create schemas.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass
