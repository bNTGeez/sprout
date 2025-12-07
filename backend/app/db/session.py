"""Database engine and session setup.

This file connects SQLAlchemy to your database using `DATABASE_URL` and
exposes `get_db()` as a FastAPI dependency that routes can use for queries.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import get_settings

settings = get_settings()
if not settings.database_url:
    raise RuntimeError(
        "DATABASE_URL is not configured. Set it in your environment or .env file."
    )

engine = create_engine(
    settings.database_url,
    echo=settings.debug, # log the SQL queries to the console
    pool_pre_ping=True, # ping the database to keep the connection alive
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
