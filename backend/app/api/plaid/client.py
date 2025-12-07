import plaid
from plaid.api import plaid_api
from ...core.config import get_settings

settings = get_settings()

if settings.plaid_env.lower() == "production":
    plaid_host = plaid.Environment.Production
else:
    plaid_host = plaid.Environment.Sandbox

if not settings.plaid_client_id or not settings.plaid_secret:
    raise ValueError(
        "Plaid credentials not configured. Please set PLAID_CLIENT_ID and PLAID_SECRET in your .env file."
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