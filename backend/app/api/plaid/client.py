import plaid
from plaid.api import plaid_api
from ...core.config import get_settings

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
client = plaid_api.PlaidApi(api_client)