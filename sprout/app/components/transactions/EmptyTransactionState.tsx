import { Search, DollarSign } from "lucide-react";

interface EmptyTransactionStateProps {
  hasFilters?: boolean;
}

export function EmptyTransactionState({
  hasFilters = false,
}: EmptyTransactionStateProps) {
  if (hasFilters) {
    return (
      <div className="flex flex-col items-center justify-center py-12 px-4">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <Search className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">
          No transactions found
        </h3>
        <p className="text-sm text-gray-500 text-center max-w-sm">
          Try adjusting your filters or search terms to find what you're looking
          for.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4">
      <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
        <DollarSign className="w-8 h-8 text-blue-600" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-1">
        No transactions yet
      </h3>
      <p className="text-sm text-gray-500 text-center max-w-sm mb-4">
        Connect your bank account or add a manual transaction to get started
        tracking your spending.
      </p>
      <div className="flex gap-3">
        <button
          type="button"
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          Add Transaction
        </button>
        <button
          type="button"
          className="px-4 py-2 bg-white text-gray-700 text-sm font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
        >
          Connect Bank
        </button>
      </div>
    </div>
  );
}
