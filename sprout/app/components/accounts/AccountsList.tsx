import { Account } from "@/app/types/accounts";
import { PlaidItem } from "@/lib/api";
import { formatCurrency } from "@/lib/accounts";
import PlaidItemCard from "./PlaidItemCard";
import ManualAccountsCard from "./ManualAccountsCard";

interface AccountsListProps {
  accounts: Account[];
  plaidItems: PlaidItem[];
}

export default function AccountsList({ accounts, plaidItems }: AccountsListProps) {
  const activeAccounts = accounts.filter((a) => a.is_active);
  
  const totalBalance = activeAccounts.reduce(
    (sum, acc) => sum + parseFloat(acc.balance),
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
      <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-white">
        <p className="text-blue-100 text-sm mb-2">Total Net Worth</p>
        <p className="text-4xl font-bold mb-4">
          {formatCurrency(totalBalance)}
        </p>
        <div className="flex gap-4 text-sm">
          <div>
            <p className="text-blue-100">Connected Institutions</p>
            <p className="font-semibold">{plaidItemsWithAccounts.length}</p>
          </div>
          <div>
            <p className="text-blue-100">Total Accounts</p>
            <p className="font-semibold">{activeAccounts.length}</p>
          </div>
          {manualAccounts.length > 0 && (
            <div>
              <p className="text-blue-100">Manual</p>
              <p className="font-semibold">{manualAccounts.length}</p>
            </div>
          )}
        </div>
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
