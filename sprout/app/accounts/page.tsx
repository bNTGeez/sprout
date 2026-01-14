"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { fetchAccounts, fetchPlaidItems, PlaidItem } from "@/lib/api";
import AccountsList from "../components/accounts/AccountsList";
import AccountsLoading from "../components/accounts/AccountsLoading";
import EmptyAccountsState from "../components/accounts/EmptyAccountsState";
import AccountsError from "../components/accounts/AccountsError";
import ReauthModal from "../components/accounts/ReauthModal";
import AddAccountsModal from "../components/accounts/AddAccountsModal";
import { Toast } from "../components/Toast";
import { Account } from "../types/accounts";
import ConnectBank from "../components/plaid/connect_bank";

export default function AccountsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [plaidItems, setPlaidItems] = useState<PlaidItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reauthModal, setReauthModal] = useState<{ plaidItemId: number; institutionName: string } | null>(null);
  const [addAccountsModal, setAddAccountsModal] = useState<{ plaidItemId: number; institutionName: string } | null>(null);
  const [toast, setToast] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  const loadData = async (token: string) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Fetch both accounts and plaid items in parallel
      const [accountsData, plaidItemsData] = await Promise.all([
        fetchAccounts(token),
        fetchPlaidItems(token),
      ]);

      setAccounts(accountsData);
      setPlaidItems(plaidItemsData);
    } catch (err) {
      console.error("Failed to load accounts:", err);
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load accounts";
      setError(errorMessage);
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

  const handleRetry = async () => {
    const supabase = createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (session) {
      loadData(session.access_token);
    }
  };

  const handleReauth = (plaidItemId: number, institutionName: string) => {
    setReauthModal({ plaidItemId, institutionName });
  };

  const handleReauthSuccess = () => {
    setToast({ type: "success", message: "Account reconnected successfully! Syncing data..." });
    if (token) {
      loadData(token);
    }
  };

  const handleAddAccounts = (plaidItemId: number, institutionName: string) => {
    setAddAccountsModal({ plaidItemId, institutionName });
  };

  const handleAddAccountsSuccess = () => {
    setToast({ type: "success", message: "Accounts added successfully! Syncing data..." });
    if (token) {
      loadData(token);
    }
  };

  const handleDisconnect = () => {
    setToast({ type: "success", message: "Institution disconnected successfully" });
    if (token) {
      loadData(token);
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-lg font-bold text-gray-900">Accounts</h1>
          <ConnectBank />
        </div>

        {isLoading && <AccountsLoading />}

        {!isLoading && error && (
          <AccountsError message={error} onRetry={handleRetry} />
        )}

        {!isLoading && !error && accounts.length === 0 && <EmptyAccountsState />}

        {!isLoading && !error && accounts.length > 0 && (
          <AccountsList 
            accounts={accounts} 
            plaidItems={plaidItems}
            onReauth={handleReauth}
            onDisconnect={handleDisconnect}
            onAddAccounts={handleAddAccounts}
          />
        )}

        {/* Reauth Modal */}
        {reauthModal && token && (
          <ReauthModal
            isOpen={true}
            plaidItemId={reauthModal.plaidItemId}
            institutionName={reauthModal.institutionName}
            token={token}
            onClose={() => setReauthModal(null)}
            onSuccess={handleReauthSuccess}
          />
        )}

        {/* Add Accounts Modal */}
        {addAccountsModal && (
          <AddAccountsModal
            isOpen={true}
            institutionName={addAccountsModal.institutionName}
            onClose={() => setAddAccountsModal(null)}
            onSuccess={handleAddAccountsSuccess}
          />
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
    </div>
  );
}
