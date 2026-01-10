import { AlertCircle, RefreshCw } from "lucide-react";

interface AccountsErrorProps {
  message: string;
  onRetry: () => void;
}

export default function AccountsError({ message, onRetry }: AccountsErrorProps) {
  return (
    <div className="text-center py-16">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-red-50 rounded-full mb-4">
        <AlertCircle className="w-8 h-8 text-red-500" />
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        Failed to load accounts
      </h3>
      <p className="text-gray-500 mb-6 max-w-sm mx-auto">{message}</p>
      <button
        onClick={onRetry}
        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        Try Again
      </button>
    </div>
  );
}
