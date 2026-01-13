"""Plaid API client factory.

Import get_plaid_client() and call it to get the Plaid client instance.
This lazy-loading approach prevents import-time crashes in tests.
"""

import plaid
from plaid.api import plaid_api
from ...core.config import get_settings

_client = None

def get_plaid_client():
    """Lazy-load Plaid client to avoid import-time crashes in tests.
    
    This function is called by routes and services at runtime, but can be
    mocked in tests before any code paths invoke it.
    
    Returns:
        PlaidApi: Configured Plaid API client instance
    """
    global _client
    if _client is not None:
        return _client
    
    settings = get_settings()
    
    plaid_env = (settings.plaid_env or "sandbox").lower()
    if plaid_env == "production":
        plaid_host = plaid.Environment.Production
    elif plaid_env == "development":
        plaid_host = plaid.Environment.Development
    else:
        plaid_host = plaid.Environment.Sandbox

    if not settings.plaid_client_id or not settings.plaid_secret:
        raise ValueError(
            "Plaid credentials not configured. Please set PLAID_CLIENT_ID, PLAID_SECRET, and PLAID_ENV in your .env file."
        )

    configuration = plaid.Configuration(
        host=plaid_host,
        api_key={
            'clientId': settings.plaid_client_id,
            'secret': settings.plaid_secret,
        }
    )

    api_client = plaid.ApiClient(configuration)
    _client = plaid_api.PlaidApi(api_client)
    return _client