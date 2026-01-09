import { AlertCircle, RefreshCw } from "lucide-react";

interface TransactionErrorProps {
  error: Error;
  onRetry: () => void;
}

export function TransactionError({ error, onRetry }: TransactionErrorProps) {
  return (
    <div className="bg-white rounded-lg shadow p-12">
      <div className="flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-red-600" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">
          Failed to load transactions
        </h3>
        <p className="text-sm text-gray-500 text-center max-w-sm mb-4">
          {error.message || "An unexpected error occurred. Please try again."}
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Retry
        </button>
      </div>
    </div>
  );
}
