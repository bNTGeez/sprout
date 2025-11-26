from functools import lru_cache
import os

from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    """Application configuration pulled from environment variables."""

    database_url: str = ""
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    load_dotenv()
    debug_value = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
    return Settings(
        database_url=os.getenv("DATABASE_URL", ""),
        debug=debug_value,
    )
