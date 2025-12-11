"""Application configuration and environment variables.

This file defines the `Settings` object and a `get_settings()` helper that
you can import anywhere in the backend to read config (e.g. database URL).
"""

from functools import lru_cache
import os

from dotenv import load_dotenv
from pydantic import BaseModel 


class Settings(BaseModel):
    """Application configuration pulled from environment variables."""

    database_url: str = ""
    debug: bool = False
    # Plaid configuration
    plaid_client_id: str = ""
    plaid_secret: str = ""
    plaid_env: str = "sandbox"  # sandbox, development, or production
    supabase_url: str = ""
    supabase_jwt_secret: str = ""

# cache the settings so we don't have to load the .env file every time
@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    load_dotenv()
    debug_value = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
    return Settings(
        database_url=os.getenv("DATABASE_URL", ""),
        debug=debug_value,
        plaid_client_id=os.getenv("PLAID_CLIENT_ID", os.getenv("plaid_client_id", "")),
        plaid_secret=os.getenv("PLAID_SECRET", os.getenv("plaid_secret", "")),
        plaid_env=os.getenv("PLAID_ENV", os.getenv("plaid_env", "sandbox")),
        supabase_url=os.getenv("SUPABASE_URL", os.getenv("supabase_url", "")),
        supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET", os.getenv("supabase_jwt_secret", "")),
    )
