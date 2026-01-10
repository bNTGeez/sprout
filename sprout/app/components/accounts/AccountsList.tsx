import { Account } from "@/app/types/accounts";
import { formatCurrency } from "@/lib/accounts";
import { Building2 } from "lucide-react";
import AccountCard from "./AccountCard";

interface AccountsListProps {
  accounts: Account[];
}

export default function AccountsList({ accounts }: AccountsListProps) {
  const activeAccounts = accounts.filter((a) => a.is_active);
  const inactiveAccounts = accounts.filter((a) => !a.is_active);

  const totalBalance = activeAccounts.reduce(
    (sum, acc) => sum + parseFloat(acc.balance),
    0
  );

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
            <p className="text-blue-100">Active Accounts</p>
            <p className="font-semibold">{activeAccounts.length}</p>
          </div>
          {inactiveAccounts.length > 0 && (
            <div>
              <p className="text-blue-100">Inactive</p>
              <p className="font-semibold">{inactiveAccounts.length}</p>
            </div>
          )}
        </div>
      </div>

      {/* Active Accounts */}
      {activeAccounts.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Active Accounts
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {activeAccounts.map((account) => (
              <AccountCard key={account.id} account={account} />
            ))}
          </div>
        </div>
      )}

      {/* Inactive Accounts */}
      {inactiveAccounts.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-500 mb-4">
            Inactive Accounts
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {inactiveAccounts.map((account) => (
              <AccountCard key={account.id} account={account} />
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {accounts.length === 0 && (
        <div className="text-center py-12">
          <Building2 className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No accounts found</p>
        </div>
      )}
    </div>
  );
}
