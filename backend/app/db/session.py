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
    echo=settings.debug,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
