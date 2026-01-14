from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal
import logging
from ...db.models import PlaidItem, Account, Transaction
from .client import get_plaid_client
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from ...schemas import AccountData
from datetime import datetime, date

logger = logging.getLogger(__name__)

def sync_accounts(plaid_item_id: int, db: Session) -> list[Account]:
  query = select(PlaidItem).filter(PlaidItem.id == plaid_item_id)
  plaid_item = db.execute(query).scalar_one_or_none()
  if not plaid_item:
    raise ValueError(f"Plaid item with id {plaid_item_id} not found")

  # Get accounts from Plaid
  client = get_plaid_client()
  request = AccountsGetRequest(access_token=plaid_item.access_token)
  response = client.accounts_get(request)
  
  # Plaid SDK returns a response object, convert to dict if needed
  if hasattr(response, 'to_dict'):
    response_dict = response.to_dict()
    accounts = response_dict.get('accounts', [])
  elif isinstance(response, dict):
    accounts = response.get('accounts', [])
  else:
    # Try to access as attribute
    accounts = getattr(response, 'accounts', [])
  
  if not accounts:
    return [] 
  
  synced_accounts = []
  for plaid_account in accounts:
    try:
      # Handle both dict and object responses from Plaid SDK
      if hasattr(plaid_account, 'to_dict'):
        account_dict = plaid_account.to_dict()
      elif isinstance(plaid_account, dict):
        account_dict = plaid_account
      else:
        # Access as attributes - convert to dict
        account_dict = {
          'account_id': getattr(plaid_account, 'account_id', None),
          'name': getattr(plaid_account, 'name', ''),
          'official_name': getattr(plaid_account, 'official_name', None),
          'type': getattr(plaid_account, 'type', ''),
          'subtype': getattr(plaid_account, 'subtype', ''),
          'mask': getattr(plaid_account, 'mask', ''),
        }
        # Handle balances object
        balances_obj = getattr(plaid_account, 'balances', None)
        if balances_obj:
          if hasattr(balances_obj, 'to_dict'):
            account_dict['balances'] = balances_obj.to_dict()
          elif isinstance(balances_obj, dict):
            account_dict['balances'] = balances_obj
          else:
            account_dict['balances'] = {'current': getattr(balances_obj, 'current', 0)}
        else:
          account_dict['balances'] = {'current': 0}
      
      account_id = account_dict.get('account_id')
      if not account_id:
        continue
      
      # Check for existing account by plaid_account_id (globally, not just this plaid_item)
      # This prevents duplicates when reconnecting the same bank account
      account_query = select(Account).filter(
        Account.plaid_account_id == account_id
      )
      existing_account = db.execute(account_query).scalar_one_or_none()
      
      # Map Plaid type/subtype to match dashboard account types
      plaid_type = account_dict.get('type', '')
      plaid_subtype = account_dict.get('subtype', '')
      
      if plaid_type == 'depository':
        account_type = plaid_subtype if plaid_subtype in ['checking', 'savings'] else 'checking'
      elif plaid_type == 'credit':
        account_type = 'credit_card'
      elif plaid_type == 'investment':
        account_type = 'brokerage'
      else:
        account_type = plaid_subtype if plaid_subtype else plaid_type
      
      # Get account name and balance
      account_name = account_dict.get('official_name') or account_dict.get('name', '')
      balances = account_dict.get('balances', {})
      balance = balances.get('current', 0) if isinstance(balances, dict) else 0
      account_mask = account_dict.get('mask', '')
      
      accountData = AccountData(
        plaid_account_id=account_id,
        name=account_name,
        account_type=account_type,
        provider="plaid",
        account_num=account_mask,
        balance=balance,
        is_active=True
      )
      
      if existing_account:
        # Update existing account with latest data and link to current plaid_item
        existing_account.name = accountData.name
        existing_account.account_type = accountData.account_type
        existing_account.account_num = accountData.account_num
        existing_account.balance = Decimal(str(accountData.balance))
        existing_account.is_active = accountData.is_active
        existing_account.plaid_item_id = plaid_item_id  # Update to current plaid_item
        synced_accounts.append(existing_account)
      else:
        # Create new account 
        account_dict = accountData.model_dump()
        account_dict['user_id'] = plaid_item.user_id
        account_dict['plaid_item_id'] = plaid_item.id
        account_dict['balance'] = Decimal(str(account_dict['balance']))
        new_account = Account(**account_dict)
        db.add(new_account)
        synced_accounts.append(new_account)
    except Exception:
      continue
  
  # Commit all changes
  db.commit()

  # Refresh objects to get IDs and updated timestamps
  for account in synced_accounts:
    db.refresh(account)
  
  return synced_accounts

def normalize_amount(plaid_transaction: dict, account_type: str) -> Decimal:
    """
    Convert Plaid transaction amount to our convention.
    
    Plaid's convention:
    - amount > 0 = outflow (debit/money leaving account)
    - amount < 0 = inflow (credit/money entering account)
    
    Our convention:
    - Positive = money coming in (income)
    - Negative = money going out (expense)
    
    Solution: Simply flip Plaid's sign (multiply by -1).
    No need to guess from descriptions - Plaid already encodes direction via sign.
    """
    raw_amount = Decimal(str(plaid_transaction.get("amount", 0)))
    
    # Get transaction details for logging
    merchant_name = plaid_transaction.get("merchant_name") or plaid_transaction.get("name") or ""
    tx_type = plaid_transaction.get("transaction_type", "unknown")
    
    # Log what Plaid gave us vs what we're storing
    normalized_amount = -raw_amount  # Flip sign: Plaid >0 (outflow) → our <0 (expense), Plaid <0 (inflow) → our >0 (income)
    
    logger.debug(
        f"Normalizing transaction: name={merchant_name}, "
        f"account_type={account_type}, tx_type={tx_type}, "
        f"plaid_amount={raw_amount}, normalized_amount={normalized_amount}"
    )
    
    return normalized_amount


def sync_transactions(plaid_item_id: int, db: Session) -> dict:
  query = select(PlaidItem).filter(PlaidItem.id == plaid_item_id)
  plaid_item = db.execute(query).scalar_one_or_none()
  if not plaid_item:
    raise ValueError(f"Plaid item with id {plaid_item_id} not found")

  account_query = select(Account).filter(Account.plaid_item_id == plaid_item_id)
  accounts = db.execute(account_query).scalars().all()
  account_map = {acc.plaid_account_id: acc.id for acc in accounts}
  account_type_map = {acc.plaid_account_id: acc.account_type for acc in accounts}

  # Start with stored cursor if available (for incremental syncs)
  # For first sync, cursor should be empty string, not None
  cursor = plaid_item.transactions_cursor or ""
  total_added = 0
  total_modified = 0
  total_removed = 0
  
  client = get_plaid_client()
  
  while True:
    # Call Plaid API
    request = TransactionsSyncRequest(
      access_token=plaid_item.access_token,
      cursor=cursor
    )
    response = client.transactions_sync(request)

    # Process added transactions
    for plaid_tx in response['added']:
      # Handle both dict and object responses
      if hasattr(plaid_tx, 'to_dict'):
        tx_dict = plaid_tx.to_dict()
      elif isinstance(plaid_tx, dict):
        tx_dict = plaid_tx
      else:
        # Skip if we can't process it
        continue
      
      plaid_account_id = tx_dict.get('account_id')
      account_id = account_map.get(plaid_account_id)
      if not account_id:
        continue  # Skip if account not found

      # Check for duplicates
      existing = db.execute(
        select(Transaction).filter(
          Transaction.plaid_transaction_id == tx_dict.get('transaction_id')
        )
      ).scalar_one_or_none()
      if existing:
        continue  # Skip duplicate

      # Normalize amount and parse date
      account_type = account_type_map.get(plaid_account_id, "checking")
      amount = normalize_amount(tx_dict, account_type)
      # Handle date - Plaid SDK may return date object or string
      date_value = tx_dict.get("date")
      if isinstance(date_value, str):
        tx_date = datetime.strptime(date_value, "%Y-%m-%d").date()
      else:
        # Already a date object
        tx_date = date_value if isinstance(date_value, date) else date_value.date()

      # Create new transaction
      new_tx = Transaction(
        user_id=plaid_item.user_id,
        account_id=account_id,  
        amount=amount,
        date=tx_date,
        description=tx_dict.get("merchant_name") or tx_dict.get("name", "Unknown"),
        plaid_transaction_id=tx_dict.get("transaction_id"),
        provider_tx_id=tx_dict.get("transaction_id"),
        category_id=None,
        normalized_merchant=None,
        is_subscription=False,
        tags=None,
        notes=None
      )

      db.add(new_tx)
      total_added += 1

    # Process modified transactions
    for plaid_tx in response["modified"]:
      # Handle both dict and object responses
      if hasattr(plaid_tx, 'to_dict'):
        tx_dict = plaid_tx.to_dict()
      elif isinstance(plaid_tx, dict):
        tx_dict = plaid_tx
      else:
        continue
      
      existing = db.execute(
        select(Transaction).filter(
          Transaction.plaid_transaction_id == tx_dict.get("transaction_id")
        )
      ).scalar_one_or_none()

      if not existing:
        continue  
      # Update fields
      account_type = account_type_map.get(tx_dict.get("account_id"), "checking")
      existing.amount = normalize_amount(tx_dict, account_type)
      # Handle date - Plaid SDK may return date object or string
      date_value = tx_dict.get("date")
      if isinstance(date_value, str):
        tx_date = datetime.strptime(date_value, "%Y-%m-%d").date()
      else:
        # Already a date object
        tx_date = date_value if isinstance(date_value, date) else date_value.date()
      existing.date = tx_date
      existing.description = tx_dict.get("merchant_name") or tx_dict.get("name", "Unknown")
      total_modified += 1
    
    # Process removed transactions
    for removed_id in response["removed"]:
      deleted = db.execute(
        select(Transaction).filter(
          Transaction.plaid_transaction_id == removed_id
        )
      ).scalar_one_or_none()

      if deleted:
        db.delete(deleted)
        total_removed += 1

    # Update cursor for next request (or to save final state)
    cursor = response["next_cursor"]
    
    # Check if more data available
    if not response["has_more"]:
      break  # No more data, we're done

  # Commit all changes
  db.commit()

  plaid_item.transactions_cursor = cursor
  db.commit()

  return {
    "added": total_added,
    "modified": total_modified,
    "removed": total_removed
  }


def renormalize_existing_transactions(plaid_item_id: int, db: Session) -> dict:
  """Re-normalize existing transactions for a PlaidItem based on their stored descriptions.
  
  WARNING: This function cannot fix sign issues. Since normalization now simply flips Plaid's sign,
  and we don't have access to Plaid's original amounts, we cannot reconstruct what Plaid originally sent.
  To fix transactions with incorrect signs, you must disconnect and reconnect the Plaid item to get
  fresh data from Plaid with the correct normalization applied.
  
  This function may be useful for other normalization changes (e.g., description-based categorization),
  but not for sign corrections.
  """
  # Get all accounts for this PlaidItem
  accounts = db.execute(
    select(Account).filter(Account.plaid_item_id == plaid_item_id)
  ).scalars().all()
  
  account_ids = [acc.id for acc in accounts]
  account_type_map = {acc.id: acc.account_type for acc in accounts}
  
  if not account_ids:
    return {"renormalized": 0}
  
  # Get all transactions for these accounts
  transactions = db.execute(
    select(Transaction).filter(
      Transaction.account_id.in_(account_ids),
      Transaction.plaid_transaction_id.isnot(None)  # Only Plaid transactions
    )
  ).scalars().all()
  
  renormalized_count = 0
  
  for tx in transactions:
    account_type = account_type_map.get(tx.account_id, "checking")
    
    # Reconstruct a Plaid-like transaction dict from stored data
    # Since normalization is now just a sign flip, we reverse it to get back to Plaid's convention
    # Our stored amount (positive=income, negative=expense) → Plaid amount (positive=outflow, negative=inflow)
    plaid_amount = -float(tx.amount)  # Reverse our normalization
    
    # Infer transaction_type based on Plaid's convention
    # Plaid positive = outflow = debit, Plaid negative = inflow = credit
    inferred_tx_type = "debit" if plaid_amount > 0 else "credit"
    
    plaid_like_dict = {
      "amount": plaid_amount,
      "transaction_type": inferred_tx_type,
      "name": tx.description,  # Use stored description
      "merchant_name": tx.normalized_merchant or tx.description
    }
    
    # Re-normalize using current logic (which just flips the sign)
    new_amount = normalize_amount(plaid_like_dict, account_type)
    
    # Only update if amount changed
    if new_amount != tx.amount:
      tx.amount = new_amount
      renormalized_count += 1
  
  db.commit()
  
  return {"renormalized": renormalized_count}