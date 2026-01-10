"use client";

import { useState, useRef, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import { triggerPlaidSync, fetchPlaidItemStatus } from "@/lib/api";

interface ManualSyncButtonProps {
  plaidItemId: number;
  institutionName: string;
  token: string;
  onSyncComplete?: (stats: {
    accounts_synced: number;
    transactions_synced: number;
  }) => void;
  onError?: (error: string) => void;
  variant?: "primary" | "secondary";
  size?: "sm" | "md" | "lg";
}

export default function ManualSyncButton({
  plaidItemId,
  institutionName,
  token,
  onSyncComplete,
  onError,
  variant = "primary",
  size = "md",
}: ManualSyncButtonProps) {
  const [isSyncing, setIsSyncing] = useState(false);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Clear polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const startPolling = () => {
    // Poll status every 2 seconds during sync
    pollingIntervalRef.current = setInterval(async () => {
      try {
        const status = await fetchPlaidItemStatus(token, plaidItemId);
        console.log(`Polling ${institutionName} status:`, status);
        // Could add logic here to detect when sync is complete
        // For now, we rely on the initial API response
      } catch (error) {
        console.error("Polling error:", error);
      }
    }, 2000);
  };

  const stopPolling = () => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  };

  const handleSync = async () => {
    try {
      setIsSyncing(true);
      startPolling();

      const result = await triggerPlaidSync(token, plaidItemId);

      // Stop polling after sync completes
      stopPolling();

      // Show success
      if (onSyncComplete) {
        const totalTransactions =
          result.transactions.added +
          result.transactions.modified +
          result.transactions.removed;
        onSyncComplete({
          accounts_synced: result.accounts_synced,
          transactions_synced: totalTransactions,
        });
      }
    } catch (error) {
      stopPolling();
      console.error("Sync failed:", error);
      const errorMessage =
        error instanceof Error ? error.message : "Sync failed";
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setIsSyncing(false);
    }
  };

  const getButtonClasses = () => {
    const baseClasses =
      "flex items-center gap-2 rounded-lg transition-colors disabled:cursor-not-allowed";

    const sizeClasses = {
      sm: "px-3 py-1.5 text-sm",
      md: "px-4 py-2",
      lg: "px-6 py-3 text-lg",
    };

    const variantClasses = {
      primary: "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300",
      secondary:
        "border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400",
    };

    return `${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]}`;
  };

  const getIconSize = () => {
    switch (size) {
      case "sm":
        return "w-3 h-3";
      case "lg":
        return "w-5 h-5";
      default:
        return "w-4 h-4";
    }
  };

  return (
    <button
      onClick={handleSync}
      disabled={isSyncing}
      className={getButtonClasses()}
      title={`Sync ${institutionName}`}
    >
      <RefreshCw
        className={`${getIconSize()} ${isSyncing ? "animate-spin" : ""}`}
      />
      {isSyncing ? "Syncing..." : "Sync Now"}
    </button>
  );
}
