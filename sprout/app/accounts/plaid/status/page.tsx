"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { fetchPlaidItems, fetchPlaidItemStatus, PlaidItem, PlaidItemStatus } from "@/lib/api";
import PlaidSyncStatus from "@/app/components/accounts/PlaidSyncStatus";
import SyncAllButton from "@/app/components/accounts/SyncAllButton";
import { Toast } from "@/app/components/Toast";
import { ArrowLeft, RefreshCw } from "lucide-react";
import Link from "next/link";

export default function PlaidStatusPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [plaidItems, setPlaidItems] = useState<PlaidItem[]>([]);
  const [statuses, setStatuses] = useState<Map<number, PlaidItemStatus>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  const loadData = async (accessToken: string) => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch plaid items
      const items = await fetchPlaidItems(accessToken);
      setPlaidItems(items);

      // Fetch status for each item
      const statusMap = new Map<number, PlaidItemStatus>();
      await Promise.all(
        items.map(async (item) => {
          try {
            const status = await fetchPlaidItemStatus(accessToken, item.id);
            statusMap.set(item.id, status);
          } catch (err) {
            console.error(`Failed to load status for item ${item.id}:`, err);
          }
        })
      );

      setStatuses(statusMap);
    } catch (err) {
      console.error("Failed to load Plaid status:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    async function checkAuth() {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session) {
        router.push("/login");
        return;
      }

      setToken(session.access_token);
      loadData(session.access_token);
    }

    checkAuth();
  }, [router]);

  const handleRefreshAll = () => {
    if (token) {
      loadData(token);
    }
  };

  const handleSyncComplete = () => {
    if (token) {
      loadData(token);
    }
  };

  const handleSyncSuccess = (message: string) => {
    setToast({ type: "success", message });
  };

  const handleSyncError = (message: string) => {
    setToast({ type: "error", message });
  };

  const handleSyncAllComplete = (totalAccounts: number, totalTransactions: number) => {
    setToast({
      type: "success",
      message: `Synced all institutions: ${totalAccounts} accounts, ${totalTransactions} transactions`,
    });
    if (token) {
      loadData(token);
    }
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="text-center py-12">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={handleRefreshAll}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/accounts"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Accounts
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Plaid Sync Status</h1>
            <p className="text-gray-500 mt-1">
              Monitor and manage your connected bank accounts
            </p>
          </div>
          <button
            onClick={handleRefreshAll}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh All
          </button>
        </div>
      </div>

      {/* Status Cards */}
      {plaidItems.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border">
          <p className="text-gray-500">No Plaid connections found</p>
          <Link
            href="/accounts"
            className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Connect a Bank
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {plaidItems.map((item) => {
            const status = statuses.get(item.id);
            if (!status || !token) return null;

            return (
              <PlaidSyncStatus
                key={item.id}
                status={status}
                token={token}
                onSyncComplete={handleSyncComplete}
                onSuccess={handleSyncSuccess}
                onError={handleSyncError}
              />
            );
          })}
        </div>
      )}

      {/* Toast Notifications */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
