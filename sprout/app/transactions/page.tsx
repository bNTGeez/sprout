"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Plus, ChevronLeft, ChevronRight } from "lucide-react";
import { TransactionTable } from "../components/transactions/TransactionTable";
import { TransactionFilters as TransactionFiltersComponent } from "../components/transactions/TransactionFilters";
import { ManualTransactionForm } from "../components/transactions/ManualTransactionForm";
import { BatchProcessingButton } from "../components/transactions/BatchProcessingButton";
import { Toast, ToastType } from "../components/Toast";
import { createClient } from "@/lib/supabase/client";
import {
  fetchCategories,
  fetchAccounts,
  createTransaction,
  fetchGoals,
  fetchTransactionStats,
} from "@/lib/api";
import type {
  TransactionFilters,
  Category,
  Account,
  TransactionCreateRequest,
} from "@/app/types/transactions";
import type { Goal } from "@/app/types/goals";

function toISODate(d: Date): string {
  // YYYY-MM-DD in local time
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getMonthRange(
  year: number,
  month1to12: number
): { date_from: string; date_to: string } {
  const start = new Date(year, month1to12 - 1, 1);
  const end = new Date(year, month1to12, 0); // last day of month
  return { date_from: toISODate(start), date_to: toISODate(end) };
}

function TransactionsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [token, setToken] = useState<string>("");
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: ToastType;
  } | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [stats, setStats] = useState<{
    total: number;
    income: number;
    expenses: number;
  }>({ total: 0, income: 0, expenses: 0 });

  // Get page from URL params, default to 1
  const currentPage = parseInt(searchParams.get("page") || "1", 10);

  // Month/year navigation (defaults to current month/year)
  const selectedYear = useMemo(() => {
    const y = parseInt(searchParams.get("year") || "", 10);
    return Number.isFinite(y) && y >= 1970 ? y : new Date().getFullYear();
  }, [searchParams.get("year")]);

  const selectedMonth = useMemo(() => {
    const m = parseInt(searchParams.get("month") || "", 10);
    return Number.isFinite(m) && m >= 1 && m <= 12
      ? m
      : new Date().getMonth() + 1;
  }, [searchParams.get("month")]);

  const monthLabel = useMemo(() => {
    const d = new Date(selectedYear, selectedMonth - 1, 1);
    return d.toLocaleString("en-US", { month: "long", year: "numeric" });
  }, [selectedYear, selectedMonth]);

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

  // Fetch categories, accounts, and goals for filters and badges
  useEffect(() => {
    const loadFiltersData = async () => {
      if (!token) return;

      try {
        const [categoriesData, accountsData, goalsData] = await Promise.all([
          fetchCategories(token),
          fetchAccounts(token),
          fetchGoals(token, true), // Only active goals
        ]);
        setCategories(categoriesData);
        setAccounts(accountsData);
        setGoals(goalsData);
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

  const handleMonthChange = (direction: "prev" | "next") => {
    const d = new Date(selectedYear, selectedMonth - 1, 1);
    d.setMonth(d.getMonth() + (direction === "next" ? 1 : -1));

    const params = new URLSearchParams(searchParams.toString());
    params.set("year", String(d.getFullYear()));
    params.set("month", String(d.getMonth() + 1));
    params.set("page", "1"); // reset paging when switching months
    router.push(`/transactions?${params.toString()}`);
  };

  const handleFilterChange = (
    newFilters: Omit<TransactionFilters, "page" | "limit">
  ) => {
    // Reset to page 1 when filters change
    const params = new URLSearchParams();
    params.set("page", "1");
    params.set("year", String(selectedYear));
    params.set("month", String(selectedMonth));

    // Add all filter params to URL
    if (newFilters.search) params.set("search", newFilters.search);
    if (newFilters.category_id)
      params.set("category_id", newFilters.category_id.toString());
    if (newFilters.min_amount) params.set("min_amount", newFilters.min_amount);
    if (newFilters.max_amount) params.set("max_amount", newFilters.max_amount);
    if (newFilters.is_uncategorized) params.set("is_uncategorized", "true");

    router.push(`/transactions?${params.toString()}`);
  };

  const handleClearFilters = () => {
    // Clear all filters and reset to page 1
    router.push(
      `/transactions?page=1&year=${selectedYear}&month=${selectedMonth}`
    );
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
    const minAmount = searchParams.get("min_amount");
    const maxAmount = searchParams.get("max_amount");
    const isUncategorized = searchParams.get("is_uncategorized");
    const { date_from, date_to } = getMonthRange(selectedYear, selectedMonth);

    return {
      page: currentPage,
      limit: 50,
      search: search || undefined,
      category_id: categoryId ? parseInt(categoryId, 10) : undefined,
      date_from,
      date_to,
      min_amount: minAmount || undefined,
      max_amount: maxAmount || undefined,
      is_uncategorized: isUncategorized === "true" || undefined,
    };
  }, [
    currentPage,
    selectedYear,
    selectedMonth,
    searchParams.get("search"),
    searchParams.get("category_id"),
    searchParams.get("min_amount"),
    searchParams.get("max_amount"),
    searchParams.get("is_uncategorized"),
  ]);

  // Calculate stats from all matching transactions (server-side aggregate)
  useEffect(() => {
    const calculateStats = async () => {
      if (!token) return;

      try {
        const data = await fetchTransactionStats(token, filters);

        setStats({
          total: data.total,
          income: data.income,
          expenses: data.expenses,
        });
      } catch (error) {
        console.error("Failed to calculate stats:", error);
      }
    };

    calculateStats();
  }, [token, filters, refreshTrigger]);

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
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-bold text-gray-900">Transactions</h1>
            <p className="text-sm text-gray-500">
              View and manage your transactions
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

        {/* Month Navigation */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleMonthChange("prev")}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50"
              aria-label="Previous month"
            >
              <ChevronLeft className="w-4 h-4 text-gray-700" />
            </button>
            <div className="text-sm font-medium text-gray-900">
              {monthLabel}
            </div>
            <button
              type="button"
              onClick={() => handleMonthChange("next")}
              className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50"
              aria-label="Next month"
            >
              <ChevronRight className="w-4 h-4 text-gray-700" />
            </button>
          </div>
          <div className="text-xs text-gray-500">
            Showing transactions for this month
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-xs text-gray-500 mb-1">Total Transactions</div>
            <div className="text-2xl font-bold font-numbers text-gray-900">
              {stats.total}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-xs text-gray-500 mb-1">Total Income</div>
            <div className="text-2xl font-bold font-numbers text-green-600">
              ${stats.income.toFixed(2)}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-xs text-gray-500 mb-1">Total Expenses</div>
            <div className="text-2xl font-bold font-numbers text-red-600">
              -${stats.expenses.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="mb-6">
          <TransactionFiltersComponent
            filters={filters}
            categories={categories}
            accounts={accounts}
            onFilterChange={handleFilterChange}
            onClearFilters={handleClearFilters}
          />
        </div>

        {/* Transaction Table */}
        <TransactionTable
          token={token}
          filters={filters}
          onPageChange={handlePageChange}
          refreshTrigger={refreshTrigger}
          categories={categories}
          goals={goals}
          onTransactionUpdate={handleTransactionUpdate}
          onError={handleError}
          onDataRefresh={handleDataRefresh}
        />
      </div>

      {/* Manual Transaction Form Modal */}
      <ManualTransactionForm
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        categories={categories}
        accounts={accounts}
        goals={goals}
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

export default function TransactionsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-6 bg-gray-50 min-h-screen">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="h-8 w-48 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-4 w-64 bg-gray-100 rounded mt-2 animate-pulse"></div>
              </div>
            </div>
          </div>
        </div>
      }
    >
      <TransactionsPageContent />
    </Suspense>
  );
}
