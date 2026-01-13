"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Plus, Pencil, Trash2, ChevronLeft, ChevronRight, Calendar, Save, Check, Wallet } from "lucide-react";
import { getCategoryIcon } from "@/lib/categoryIcons";
import { createClient } from "@/lib/supabase/client";
import {
  fetchBudgets,
  fetchCategories,
  createBudget,
  updateBudget,
  deleteBudget,
} from "@/lib/api";
import { BudgetForm } from "../components/budgets/BudgetForm";
import { Toast, ToastType } from "../components/Toast";
import type { Budget, BudgetCreateRequest, BudgetUpdateRequest } from "@/app/types/budgets";
import type { Category } from "@/app/types/transactions";

export default function BudgetsPage() {
  const router = useRouter();
  const [token, setToken] = useState<string>("");
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState<Budget | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [toast, setToast] = useState<{
    message: string;
    type: ToastType;
  } | null>(null);

  // Get current month/year for initial state
  const today = new Date();
  const currentMonth = today.getMonth() + 1;
  const currentYear = today.getFullYear();

  // Selected month/year for navigation
  const [selectedMonth, setSelectedMonth] = useState<number>(currentMonth);
  const [selectedYear, setSelectedYear] = useState<number>(currentYear);

  useEffect(() => {
    const getSession = async () => {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (session?.access_token) {
        setToken(session.access_token);
      } else {
        router.push("/login");
      }
      setIsLoadingAuth(false);
    };

    getSession();
  }, [router]);

  useEffect(() => {
    const loadData = async () => {
      if (!token) return;

      try {
        setIsLoading(true);
        const [budgetsData, categoriesData] = await Promise.all([
          fetchBudgets(token, selectedMonth, selectedYear),
          fetchCategories(token),
        ]);
        setBudgets(budgetsData);
        setCategories(categoriesData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load budgets");
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [token, selectedMonth, selectedYear]);

  const handleCreateBudget = async (data: BudgetCreateRequest) => {
    try {
      await createBudget(token, data);
      setToast({
        message: "Budget created successfully!",
        type: "success",
      });
      setIsFormOpen(false);
      // Reload budgets for the selected month/year
      const budgetsData = await fetchBudgets(token, selectedMonth, selectedYear);
      setBudgets(budgetsData);
    } catch (error) {
      setToast({
        message:
          error instanceof Error
            ? error.message
            : "Failed to create budget",
        type: "error",
      });
      throw error;
    }
  };

  const handleUpdateBudget = async (data: BudgetUpdateRequest) => {
    if (!editingBudget) return;

    try {
      await updateBudget(token, editingBudget.id, data);
      setToast({
        message: "Budget updated successfully!",
        type: "success",
      });
      setIsFormOpen(false);
      setEditingBudget(null);
      // Reload budgets for the selected month/year
      const budgetsData = await fetchBudgets(token, selectedMonth, selectedYear);
      setBudgets(budgetsData);
    } catch (error) {
      setToast({
        message:
          error instanceof Error
            ? error.message
            : "Failed to update budget",
        type: "error",
      });
      throw error;
    }
  };

  const handleDeleteBudget = async (budgetId: number) => {
    if (!confirm("Are you sure you want to delete this budget?")) {
      return;
    }

    try {
      await deleteBudget(token, budgetId);
      setToast({
        message: "Budget deleted successfully!",
        type: "success",
      });
      // Reload budgets for the selected month/year
      const budgetsData = await fetchBudgets(token, selectedMonth, selectedYear);
      setBudgets(budgetsData);
    } catch (error) {
      setToast({
        message:
          error instanceof Error
            ? error.message
            : "Failed to delete budget",
        type: "error",
      });
    }
  };

  const handlePreviousMonth = () => {
    if (selectedMonth === 1) {
      setSelectedMonth(12);
      setSelectedYear(selectedYear - 1);
    } else {
      setSelectedMonth(selectedMonth - 1);
    }
  };

  const handleNextMonth = () => {
    if (selectedMonth === 12) {
      setSelectedMonth(1);
      setSelectedYear(selectedYear + 1);
    } else {
      setSelectedMonth(selectedMonth + 1);
    }
  };

  const handleMonthChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedMonth(parseInt(e.target.value));
  };

  const handleYearChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const year = parseInt(e.target.value);
    if (year >= 2000 && year <= 2100) {
      setSelectedYear(year);
    }
  };

  const goToCurrentMonth = () => {
    setSelectedMonth(currentMonth);
    setSelectedYear(currentYear);
  };

  const isCurrentMonth = selectedMonth === currentMonth && selectedYear === currentYear;

  const handleEditClick = (budget: Budget) => {
    setEditingBudget(budget);
    setIsFormOpen(true);
  };

  const handleAddClick = () => {
    setEditingBudget(null);
    setIsFormOpen(true);
  };

  const handleFormClose = () => {
    setIsFormOpen(false);
    setEditingBudget(null);
  };

  const handleFormSubmit = async (data: BudgetCreateRequest | BudgetUpdateRequest) => {
    if (editingBudget) {
      await handleUpdateBudget(data as BudgetUpdateRequest);
    } else {
      await handleCreateBudget(data as BudgetCreateRequest);
    }
  };

  if (isLoadingAuth || isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-gray-200 rounded animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
              <div className="h-6 w-32 bg-gray-200 rounded mb-4"></div>
              <div className="h-4 w-24 bg-gray-100 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-bold text-gray-900">Budgets</h1>
            {/* Month/Year Navigation */}
            <div className="flex items-center gap-2">
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                <select
                  value={selectedMonth}
                  onChange={handleMonthChange}
                  className="pl-9 pr-3 py-1.5 text-sm font-medium text-gray-900 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none cursor-pointer"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((month) => (
                    <option key={month} value={month}>
                      {new Date(2000, month - 1).toLocaleDateString("en-US", {
                        month: "long",
                      })}
                    </option>
                  ))}
                </select>
              </div>
              <input
                type="number"
                min="2000"
                max="2100"
                value={selectedYear}
                onChange={handleYearChange}
                className="w-20 px-3 py-1.5 text-sm font-medium text-gray-900 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isEditMode ? (
              <button
                type="button"
                onClick={() => setIsEditMode(false)}
                className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors flex items-center gap-2"
              >
                <Check className="w-4 h-4" />
                Save
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setIsEditMode(true)}
                className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg transition-colors flex items-center gap-2"
              >
                <Pencil className="w-4 h-4" />
                Edit
              </button>
            )}
            <button
              type="button"
              onClick={handleAddClick}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Budget
            </button>
          </div>
        </div>

        {/* Budgets Grid */}
      {budgets.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <div className="flex justify-center mb-4">
            <Wallet className="w-12 h-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No budgets yet</h3>
          <p className="text-gray-500 mb-4">
            Create your first budget to track spending by category
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {budgets.map((budget) => {
            const spent = parseFloat(budget.spent);
            const amount = parseFloat(budget.amount);
            const remaining = parseFloat(budget.remaining);
            const percentUsed = budget.percent_used;

            return (
              <div
                key={budget.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
              >
                {/* Category Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{budget.category.icon}</span>
                    <h3 className="text-lg font-semibold text-gray-900">
                      {budget.category.name}
                    </h3>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleEditClick(budget)}
                      className="text-gray-400 hover:text-blue-600 transition-colors"
                      title="Edit budget"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteBudget(budget.id)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete budget"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Budget Amount */}
                <div className="mb-4">
                  <div className="text-sm text-gray-500 mb-1 font-numbers">Budget ${amount.toFixed(2)}</div>
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        budget.is_over_budget
                          ? "bg-red-500"
                          : percentUsed > 80
                          ? "bg-yellow-500"
                          : "bg-green-500"
                      }`}
                      style={{ width: `${Math.min(percentUsed, 100)}%` }}
                    ></div>
                  </div>
                  <div className="text-sm text-gray-600 font-numbers">
                    Spent: ${spent.toFixed(2)} - {percentUsed.toFixed(1)}% used
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

        {/* Budget Form Modal */}
        <BudgetForm
          isOpen={isFormOpen}
          onClose={handleFormClose}
          categories={categories}
          budget={editingBudget}
          defaultMonth={selectedMonth}
          defaultYear={selectedYear}
          onSubmit={handleFormSubmit}
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
    </div>
  );
}
