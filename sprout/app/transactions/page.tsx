"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus } from "lucide-react";
import { TransactionTable } from "../components/transactions/TransactionTable";
import { TransactionFilters as TransactionFiltersComponent } from "../components/transactions/TransactionFilters";
import { ManualTransactionForm } from "../components/transactions/ManualTransactionForm";
import { BatchProcessingButton } from "../components/transactions/BatchProcessingButton";
import { Toast, ToastType } from "../components/Toast";
import { createClient } from "@/lib/supabase/client";
import { fetchCategories, fetchAccounts, createTransaction } from "@/lib/api";
import type {
  TransactionFilters,
  Category,
  Account,
  TransactionCreateRequest,
} from "@/app/types/transactions";

export default function TransactionsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [token, setToken] = useState<string>("");
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: ToastType;
  } | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

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

  // Fetch categories and accounts for filters
  useEffect(() => {
    const loadFiltersData = async () => {
      if (!token) return;

      try {
        const [categoriesData, accountsData] = await Promise.all([
          fetchCategories(token),
          fetchAccounts(token),
        ]);
        setCategories(categoriesData);
        setAccounts(accountsData);
      } catch (error) {
        console.error("Failed to load filter data:", error);
      }
    };

    loadFiltersData();
  }, [token]);

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

  const handleFilterChange = (
    newFilters: Omit<TransactionFilters, "page" | "limit">
  ) => {
    // Reset to page 1 when filters change
    const params = new URLSearchParams();
    params.set("page", "1");

    // Add all filter params to URL
    if (newFilters.search) params.set("search", newFilters.search);
    if (newFilters.category_id)
      params.set("category_id", newFilters.category_id.toString());
    if (newFilters.date_from) params.set("date_from", newFilters.date_from);
    if (newFilters.date_to) params.set("date_to", newFilters.date_to);
    if (newFilters.min_amount) params.set("min_amount", newFilters.min_amount);
    if (newFilters.max_amount) params.set("max_amount", newFilters.max_amount);
    if (newFilters.is_uncategorized) params.set("is_uncategorized", "true");

    router.push(`/transactions?${params.toString()}`);
  };

  const handleClearFilters = () => {
    // Clear all filters and reset to page 1
    router.push("/transactions?page=1");
  };

  const handleCreateTransaction = async (data: TransactionCreateRequest) => {
    try {
      await createTransaction(token, data);

      // Show success toast
      setToast({
        message: "Transaction added successfully!",
        type: "success",
      });

      // Trigger refresh of transaction list
      setRefreshTrigger((prev) => prev + 1);

      // Reset to page 1 to see the new transaction
      if (filters.page !== 1) {
        router.push("/transactions?page=1");
      }
    } catch (error) {
      // Show error toast
      setToast({
        message:
          error instanceof Error
            ? error.message
            : "Failed to create transaction",
        type: "error",
      });
      throw error; // Re-throw so form knows it failed
    }
  };

  const handleTransactionUpdate = () => {
    // Show success toast
    setToast({
      message: "Transaction updated successfully!",
      type: "success",
    });
  };

  const handleError = (message: string) => {
    // Show error toast
    setToast({
      message: message,
      type: "error",
    });
  };

  const handleProcessingComplete = () => {
    // Show success toast
    setToast({
      message: "All transactions categorized successfully!",
      type: "success",
    });
    // Trigger refresh
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleDataRefresh = () => {
    // Show info toast when data is refreshed
    setToast({
      message: "Transactions updated",
      type: "info",
    });
  };

  // Build filters from URL params - memoized to prevent infinite re-renders
  const filters: TransactionFilters = useMemo(() => {
    const search = searchParams.get("search");
    const categoryId = searchParams.get("category_id");
    const dateFrom = searchParams.get("date_from");
    const dateTo = searchParams.get("date_to");
    const minAmount = searchParams.get("min_amount");
    const maxAmount = searchParams.get("max_amount");
    const isUncategorized = searchParams.get("is_uncategorized");
    
    return {
      page: currentPage,
      limit: 50,
      search: search || undefined,
      category_id: categoryId ? parseInt(categoryId, 10) : undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      min_amount: minAmount || undefined,
      max_amount: maxAmount || undefined,
      is_uncategorized: isUncategorized === "true" || undefined,
    };
  }, [
    currentPage,
    searchParams.get("search"),
    searchParams.get("category_id"),
    searchParams.get("date_from"),
    searchParams.get("date_to"),
    searchParams.get("min_amount"),
    searchParams.get("max_amount"),
    searchParams.get("is_uncategorized"),
  ]);

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
        <div className="flex items-center gap-3">
          <BatchProcessingButton
            token={token}
            onProcessingComplete={handleProcessingComplete}
            onError={handleError}
          />
          <button
            type="button"
            onClick={() => setIsFormOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Transaction
          </button>
        </div>
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

      {/* Filters */}
      <TransactionFiltersComponent
        filters={filters}
        categories={categories}
        accounts={accounts}
        onFilterChange={handleFilterChange}
        onClearFilters={handleClearFilters}
      />

      {/* Transaction Table */}
      <TransactionTable
        token={token}
        filters={filters}
        onPageChange={handlePageChange}
        refreshTrigger={refreshTrigger}
        categories={categories}
        onTransactionUpdate={handleTransactionUpdate}
        onError={handleError}
        onDataRefresh={handleDataRefresh}
      />

      {/* Manual Transaction Form Modal */}
      <ManualTransactionForm
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        categories={categories}
        accounts={accounts}
        onSubmit={handleCreateTransaction}
      />

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
