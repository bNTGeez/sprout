"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus } from "lucide-react";
import { TransactionTable } from "../components/transactions/TransactionTable";
import { createClient } from "@/lib/supabase/client";
import type { TransactionFilters } from "@/app/types/transactions";

export default function TransactionsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [token, setToken] = useState<string>("");
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);

  // Get page from URL params, default to 1
  const currentPage = parseInt(searchParams.get("page") || "1", 10);

  useEffect(() => {
    const getSession = async () => {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session?.access_token) {
        setToken(session.access_token);
      }
      setIsLoadingAuth(false);
    };

    getSession();
  }, []);

  // Validate and fix page number if invalid
  useEffect(() => {
    if (currentPage < 1) {
      // If page is less than 1, redirect to page 1
      router.replace("/transactions?page=1");
    }
  }, [currentPage, router]);

  const handlePageChange = (page: number) => {
    // Update URL with new page number
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", page.toString());
    router.push(`/transactions?${params.toString()}`);
  };

  // Build filters from URL params
  const filters: TransactionFilters = {
    page: currentPage,
    limit: 50, // Default limit
  };

  if (isLoadingAuth || !token) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-8 w-48 bg-gray-200 rounded animate-pulse"></div>
            <div className="h-4 w-64 bg-gray-100 rounded mt-2 animate-pulse"></div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-lg shadow p-4 animate-pulse"
            >
              <div className="h-4 w-24 bg-gray-200 rounded mb-2"></div>
              <div className="h-8 w-32 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transactions</h1>
          <p className="mt-1 text-sm text-gray-500">
            View and manage all your transactions
          </p>
        </div>
        <button
          type="button"
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Transaction
        </button>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500 mb-1">Total Transactions</div>
          <div className="text-2xl font-bold text-gray-900">10</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500 mb-1">Total Income</div>
          <div className="text-2xl font-bold text-green-600">+$3,000.00</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500 mb-1">Total Expenses</div>
          <div className="text-2xl font-bold text-red-600">-$1,906.04</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500 mb-1">Uncategorized</div>
          <div className="text-2xl font-bold text-orange-600">1</div>
        </div>
      </div>

      {/* Transaction Table */}
      <TransactionTable
        token={token}
        filters={filters}
        onPageChange={handlePageChange}
      />
    </div>
  );
}
