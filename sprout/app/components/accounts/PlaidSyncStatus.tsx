"use client";

import { useState } from "react";
import { CheckCircle, AlertCircle, Clock } from "lucide-react";
import { PlaidItemStatus } from "@/lib/api";
import ManualSyncButton from "./ManualSyncButton";

interface PlaidSyncStatusProps {
  status: PlaidItemStatus;
  token: string;
  onSyncComplete: () => void;
  onSuccess?: (message: string) => void;
  onError?: (message: string) => void;
}

function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return "Never";

  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export default function PlaidSyncStatus({ status, token, onSyncComplete, onSuccess, onError }: PlaidSyncStatusProps) {
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSyncComplete = (stats: { accounts_synced: number; transactions_synced: number }) => {
    setLocalError(null);
    onSyncComplete();
    if (onSuccess) {
      const message = `Synced ${status.institution_name}: ${stats.accounts_synced} accounts, ${stats.transactions_synced} transactions`;
      onSuccess(message);
    }
  };

  const handleSyncError = (error: string) => {
    setLocalError(error);
    if (onError) {
      onError(`${status.institution_name}: ${error}`);
    }
  };

  const getStatusIcon = () => {
    switch (status.status) {
      case "good":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "error":
      case "requires_reauth":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (status.status) {
      case "good":
        return "text-green-600 bg-green-50";
      case "error":
      case "requires_reauth":
        return "text-red-600 bg-red-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case "good":
        return "Connected";
      case "error":
        return "Error";
      case "requires_reauth":
        return "Needs Reauth";
      default:
        return status.status;
    }
  };

  return (
    <div className="bg-white rounded-lg border p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <div>
            <h3 className="font-semibold text-gray-900">{status.institution_name}</h3>
            <span className={`inline-block mt-1 px-2 py-1 text-xs font-medium rounded ${getStatusColor()}`}>
              {getStatusText()}
            </span>
          </div>
        </div>
        <ManualSyncButton
          plaidItemId={status.plaid_item_id}
          institutionName={status.institution_name}
          token={token}
          onSyncComplete={handleSyncComplete}
          onError={handleSyncError}
          variant="primary"
          size="md"
        />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-500 mb-1">Accounts</p>
          <p className="text-2xl font-bold text-gray-900">{status.accounts_count}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-500 mb-1">Transactions</p>
          <p className="text-2xl font-bold text-gray-900">{status.transactions_count}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-500 mb-1">Sync Cursor</p>
          <p className="text-sm font-medium text-gray-900">
            {status.has_cursor ? "Active" : "None"}
          </p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-500 mb-1">Last Synced</p>
          <p className="text-sm font-medium text-gray-900">
            {formatRelativeTime(status.last_synced)}
          </p>
        </div>
      </div>

      {/* Error Message */}
      {localError && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {localError}
        </div>
      )}

      {/* Info */}
      {status.status === "requires_reauth" && (
        <div className="flex items-start gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Reconnection Required</p>
            <p className="text-yellow-700 mt-1">
              This account needs to be reconnected. Please use Plaid Link to reauthorize.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
