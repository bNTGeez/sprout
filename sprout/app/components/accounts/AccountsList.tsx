import { Account } from "@/app/types/accounts";
import { PlaidItem } from "@/lib/api";
import { formatCurrency } from "@/lib/accounts";
import PlaidItemCard from "./PlaidItemCard";
import ManualAccountsCard from "./ManualAccountsCard";

interface AccountsListProps {
  accounts: Account[];
  plaidItems: PlaidItem[];
  onReauth?: (plaidItemId: number, institutionName: string) => void;
  onDisconnect?: () => void;
  onAddAccounts?: (plaidItemId: number, institutionName: string) => void;
}

export default function AccountsList({ accounts, plaidItems, onReauth, onDisconnect, onAddAccounts }: AccountsListProps) {
  const activeAccounts = accounts.filter((a) => a.is_active);
  
  // Calculate net worth: assets (positive) minus liabilities (credit cards, negative)
  const totalBalance = activeAccounts.reduce(
    (sum, acc) => {
      const balance = parseFloat(acc.balance);
      // Credit cards are liabilities - subtract from net worth
      if (acc.account_type === "credit_card") {
        return sum - balance; // Subtract credit card balance (it's already positive from Plaid)
      }
      // All other accounts (checking, savings, etc.) are assets - add to net worth
      return sum + balance;
    },
    0
  );

  // Group accounts by plaid_item_id
  const accountsByPlaidItem = new Map<number, Account[]>();
  const manualAccounts: Account[] = [];

  activeAccounts.forEach((account) => {
    if (account.plaid_item_id === null) {
      manualAccounts.push(account);
    } else {
      const existing = accountsByPlaidItem.get(account.plaid_item_id) || [];
      accountsByPlaidItem.set(account.plaid_item_id, [...existing, account]);
    }
  });

  // Match plaid items with their accounts
  const plaidItemsWithAccounts = plaidItems
    .map((item) => ({
      plaidItem: item,
      accounts: accountsByPlaidItem.get(item.id) || [],
    }))
    .filter((item) => item.accounts.length > 0); // Only show items that have accounts

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-blue-600 rounded-lg p-6 text-white">
        <p className="text-white text-sm mb-2">Total Net Worth</p>
        <p className="text-4xl font-bold font-numbers">
          {formatCurrency(totalBalance)}
        </p>
      </div>

      {/* Plaid Items */}
      {plaidItemsWithAccounts.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Connected Institutions
          </h2>
          {plaidItemsWithAccounts.map(({ plaidItem, accounts }) => (
            <PlaidItemCard
              key={plaidItem.id}
              plaidItem={plaidItem}
              accounts={accounts}
              onReauth={() => onReauth?.(plaidItem.id, plaidItem.institution_name)}
              onDisconnect={onDisconnect}
              onAddAccounts={() => onAddAccounts?.(plaidItem.id, plaidItem.institution_name)}
            />
          ))}
        </div>
      )}

      {/* Manual Accounts */}
      {manualAccounts.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Manual Accounts
          </h2>
          <ManualAccountsCard accounts={manualAccounts} />
        </div>
      )}
    </div>
  );
}
