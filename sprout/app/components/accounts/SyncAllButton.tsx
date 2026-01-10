"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { triggerPlaidSync, PlaidItem } from "@/lib/api";

interface SyncAllButtonProps {
  plaidItems: PlaidItem[];
  token: string;
  onSyncComplete?: (totalAccounts: number, totalTransactions: number) => void;
  onError?: (error: string) => void;
}

export default function SyncAllButton({
  plaidItems,
  token,
  onSyncComplete,
  onError,
}: SyncAllButtonProps) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });

  const handleSyncAll = async () => {
    if (plaidItems.length === 0) return;

    try {
      setIsSyncing(true);
      setProgress({ current: 0, total: plaidItems.length });

      let totalAccounts = 0;
      let totalTransactions = 0;
      const errors: string[] = [];

      // Sync each item sequentially
      for (let i = 0; i < plaidItems.length; i++) {
        const item = plaidItems[i];
        setProgress({ current: i + 1, total: plaidItems.length });

        try {
          const result = await triggerPlaidSync(token, item.id);
          totalAccounts += result.accounts_synced;
          totalTransactions += result.transactions.added + result.transactions.modified + result.transactions.removed;
        } catch (error) {
          console.error(`Failed to sync ${item.institution_name}:`, error);
          errors.push(`${item.institution_name}: ${error instanceof Error ? error.message : "Failed"}`);
        }
      }

      // Show results
      if (errors.length > 0 && onError) {
        onError(`Some syncs failed: ${errors.join(", ")}`);
      } else if (onSyncComplete) {
        onSyncComplete(totalAccounts, totalTransactions);
      }
    } catch (error) {
      console.error("Sync all failed:", error);
      if (onError) {
        onError(error instanceof Error ? error.message : "Sync all failed");
      }
    } finally {
      setIsSyncing(false);
      setProgress({ current: 0, total: 0 });
    }
  };

  return (
    <button
      onClick={handleSyncAll}
      disabled={isSyncing || plaidItems.length === 0}
      className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
    >
      <RefreshCw className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
      {isSyncing
        ? `Syncing ${progress.current}/${progress.total}...`
        : `Sync All (${plaidItems.length})`}
    </button>
  );
}
