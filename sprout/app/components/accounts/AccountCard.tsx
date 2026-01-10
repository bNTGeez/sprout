import { Account } from "@/app/types/accounts";
import {
  getAccountIcon,
  getAccountTypeLabel,
  formatCurrency,
} from "@/lib/accounts";

interface AccountCardProps {
  account: Account;
}

export default function AccountCard({ account }: AccountCardProps) {
  const balanceNum = parseFloat(account.balance);
  const isPositive = balanceNum >= 0;
  const balanceColor = isPositive ? "text-green-600" : "text-red-600";
  const Icon = getAccountIcon(account.account_type);

  return (
    <div
      className={`bg-white rounded-lg border p-6 hover:shadow-md transition-shadow ${
        !account.is_active ? "opacity-60" : ""
      }`}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={`p-2 rounded-lg ${
              isPositive
                ? "bg-green-50 text-green-600"
                : "bg-red-50 text-red-600"
            }`}
          >
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{account.name}</h3>
            <p className="text-sm text-gray-500">
              {getAccountTypeLabel(account.account_type)}
            </p>
          </div>
        </div>
        {!account.is_active && (
          <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded">
            Inactive
          </span>
        )}
      </div>

      <div className="flex items-end justify-between">
        <div>
          <p className="text-sm text-gray-500 mb-1">Balance</p>
          <p className={`text-2xl font-bold ${balanceColor}`}>
            {formatCurrency(account.balance)}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">
            {account.provider === "manual" ? "Manual" : "Plaid"}
          </p>
        </div>
      </div>
    </div>
  );
}
