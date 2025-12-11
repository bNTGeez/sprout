from typing import Annotated
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...db.models import User, PlaidItem, Account, Transaction
from ...schemas import PublicTokenRequest
from ...core.auth import get_current_user
from sqlalchemy import select
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from .client import client
from .services import sync_accounts, sync_transactions

router = APIRouter()

@router.get("/link_token/create")
def get_plaid_link(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> dict:

  try:
    request = LinkTokenCreateRequest(
      products=[Products("auth"), Products("transactions")],
      client_name="Sprout Budget App",
      country_codes=[CountryCode('US')],
      language='en',
      user=LinkTokenCreateRequestUser(
          client_user_id=str(current_user.id)
      )
    )
    response = client.link_token_create(request)
    link_token = response["link_token"]
    
    return {"link_token": link_token}
  except Exception as e:

    try:
      body = getattr(e, "body", None)
      status = getattr(e, "status", None)
      print("Plaid link_token_create error status:", status)
      print("Plaid link_token_create error body:", body)
    except Exception:
      pass
    raise HTTPException(
      status_code=500,
      detail=f"Failed to create Plaid link token: {str(e)}"
    )

@router.post("/item/public_token/exchange")
def plaid_link_callback(
    request: PublicTokenRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> dict:

  try:
    # Exchange public_token for access_token
    exchange_request = ItemPublicTokenExchangeRequest(public_token=request.public_token)  
    response = client.item_public_token_exchange(exchange_request)
    access_token = response['access_token']
    item_id = response['item_id']

    # Create PlaidItem
    plaid_item = PlaidItem(
      user_id=current_user.id, 
      plaid_item_id=item_id, 
      access_token=access_token, 
      institution_name=request.institution_name or "Unknown Institution",
      institution_id=request.institution_id or "unknown",
      status="good"
    )

    db.add(plaid_item)
    db.commit()
    db.refresh(plaid_item)

    # Sync accounts and transactions
    try:
      synced_accounts = sync_accounts(plaid_item.id, db)
      
      transactions_result = None
      try:
        transactions_result = sync_transactions(plaid_item.id, db)
      except Exception:
        # Transaction sync can fail - user can retry via sync endpoint
        pass
      
      return {
        "success": True, 
        "plaid_item_id": plaid_item.id, 
        "accounts_synced": len(synced_accounts),
        "transactions_synced": transactions_result if transactions_result else None,
        "message": "Bank account connected and synced successfully"
      }
    except Exception as sync_error:
      # If sync fails, still return success for the link
      return {
        "success": True,
        "plaid_item_id": plaid_item.id,
        "warning": f"Account linked but sync failed: {str(sync_error)}",
        "message": "Bank account connected successfully"
      }

  except Exception as e:
    db.rollback()
    raise HTTPException(
      status_code=500,
      detail=f"Failed to exchange Plaid token: {str(e)}"
    )

@router.get("/items")
def list_plaid_items(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> dict:
  """List all PlaidItems for the current user."""

  plaid_items = db.execute(
    select(PlaidItem).filter(PlaidItem.user_id == current_user.id)
    .order_by(PlaidItem.created_at.desc())
  ).scalars().all()

  return {
    "plaid_items": [
      {
        "id": item.id,
        "institution_name": item.institution_name,
        "status": item.status,
        "created_at": item.created_at.isoformat() if item.created_at else None
      }
      for item in plaid_items
    ]
  }

@router.get("/status/{plaid_item_id}")
def get_plaid_item_status(
    plaid_item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> dict:
  """Get sync status for a PlaidItem - shows account and transaction counts."""

  # Get PlaidItem
  plaid_item_query = select(PlaidItem).filter(
    PlaidItem.id == plaid_item_id,
    PlaidItem.user_id == current_user.id
  )
  plaid_item = db.execute(plaid_item_query).scalar_one_or_none()
  if not plaid_item:
    raise HTTPException(status_code=404, detail="PlaidItem not found")

  # Count accounts and transactions
  accounts = db.execute(
    select(Account).filter(Account.plaid_item_id == plaid_item_id)
  ).scalars().all()
  
  account_ids = [acc.id for acc in accounts] if accounts else []
  transactions = db.execute(
    select(Transaction).filter(
      Transaction.plaid_transaction_id.isnot(None),
      Transaction.account_id.in_(account_ids) if account_ids else False
    )
  ).scalars().all() if account_ids else []

  return {
    "plaid_item_id": plaid_item.id,
    "institution_name": plaid_item.institution_name,
    "status": plaid_item.status,
    "accounts_count": len(accounts),
    "transactions_count": len(transactions),
    "has_cursor": plaid_item.transactions_cursor is not None,
    "last_synced": plaid_item.updated_at.isoformat() if plaid_item.updated_at else None
  }

@router.post("/sync")
def sync_plaid_data(
    plaid_item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> dict:
  """Manually trigger sync for accounts and transactions for a PlaidItem."""

  # Verify PlaidItem belongs to current user
  plaid_item_query = select(PlaidItem).filter(
    PlaidItem.id == plaid_item_id,
    PlaidItem.user_id == current_user.id
  )
  plaid_item = db.execute(plaid_item_query).scalar_one_or_none()
  if not plaid_item:
    raise HTTPException(status_code=404, detail="PlaidItem not found")

  try:
    # Sync accounts
    synced_accounts = sync_accounts(plaid_item_id, db)
    
    # Sync transactions
    transactions_result = sync_transactions(plaid_item_id, db)
    
    return {
      "success": True,
      "accounts_synced": len(synced_accounts),
      "transactions": {
        "added": transactions_result["added"],
        "modified": transactions_result["modified"],
        "removed": transactions_result["removed"]
      }
    }
  except ValueError as e:
    raise HTTPException(status_code=404, detail=str(e))
  except Exception as e:
    raise HTTPException(
      status_code=500,
      detail=f"Failed to sync Plaid data: {str(e)}"
    )

