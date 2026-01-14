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
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

# cache the settings so we don't have to load the .env file every time
@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    load_dotenv()
    debug_value = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
    
    # Get Plaid environment
    plaid_env = os.getenv("PLAID_ENV", "sandbox").lower()
    
    # Support environment-specific secrets (PLAID_PROD_SECRET, PLAID_DEV_SECRET, etc.)
    # but fall back to generic PLAID_SECRET for backward compatibility
    plaid_secret = ""
    if plaid_env == "production" and os.getenv("PLAID_PROD_SECRET"):
        plaid_secret = os.getenv("PLAID_PROD_SECRET", "")
    elif plaid_env == "development" and os.getenv("PLAID_DEV_SECRET"):
        plaid_secret = os.getenv("PLAID_DEV_SECRET", "")
    else:
        plaid_secret = os.getenv("PLAID_SECRET", "")
    
    return Settings(
        database_url=os.getenv("DATABASE_URL", ""),
        debug=debug_value,
        plaid_client_id=os.getenv("PLAID_CLIENT_ID", ""),
        plaid_secret=plaid_secret,
        plaid_env=plaid_env,
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_jwt_secret=os.getenv("SUPABASE_JWT_SECRET", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
