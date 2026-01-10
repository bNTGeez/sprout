"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { fetchAccounts, fetchPlaidItems, PlaidItem } from "@/lib/api";
import AccountsList from "../components/accounts/AccountsList";
import AccountsLoading from "../components/accounts/AccountsLoading";
import EmptyAccountsState from "../components/accounts/EmptyAccountsState";
import AccountsError from "../components/accounts/AccountsError";
import { Account } from "../types/accounts";

export default function AccountsPage() {
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [plaidItems, setPlaidItems] = useState<PlaidItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Accounts</h1>
        <p className="text-gray-500 mt-1">
          Manage your connected accounts and balances
        </p>
      </div>

      {isLoading && <AccountsLoading />}

      {!isLoading && error && (
        <AccountsError message={error} onRetry={handleRetry} />
      )}

      {!isLoading && !error && accounts.length === 0 && <EmptyAccountsState />}

      {!isLoading && !error && accounts.length > 0 && (
        <AccountsList accounts={accounts} plaidItems={plaidItems} />
      )}
    </div>
  );
}
