import { Pencil, Trash2, RefreshCw } from "lucide-react";
import { CategoryBadge } from "./CategoryBadge";
import type { Transaction } from "@/app/types/transactions";

interface TransactionRowProps {
  transaction: Transaction;
}

export function TransactionRow({ transaction }: TransactionRowProps) {
  const amount = parseFloat(transaction.amount);
  const isExpense = amount < 0;
  const formattedAmount = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    signDisplay: "never",
  }).format(Math.abs(amount));

  const formattedDate = new Date(transaction.date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      {/* Date */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {formattedDate}
      </td>

      {/* Description / Merchant */}
      <td className="px-6 py-4">
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-900">
            {transaction.description}
          </span>
          {transaction.normalized_merchant && (
            <span className="text-xs text-gray-500 mt-0.5">
              {transaction.normalized_merchant}
            </span>
          )}
          {transaction.is_subscription && (
            <span className="inline-flex items-center gap-1 text-xs text-purple-600 mt-1">
              <RefreshCw className="w-3 h-3" />
              Recurring
            </span>
          )}
        </div>
      </td>

      {/* Category */}
      <td className="px-6 py-4 whitespace-nowrap">
        <CategoryBadge category={transaction.category} />
      </td>

      {/* Account */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {transaction.account.name}
      </td>

      {/* Amount */}
      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-right">
        <span className={isExpense ? "text-red-600" : "text-green-600"}>
          {isExpense ? "-" : "+"}
          {formattedAmount}
        </span>
      </td>

      {/* Actions */}
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            className="text-gray-400 hover:text-gray-600 transition-colors"
            title="Edit transaction"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            type="button"
            className="text-gray-400 hover:text-red-600 transition-colors"
            title="Delete transaction"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </td>
    </tr>
  );
}
