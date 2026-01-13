"use client";

import { useState, useEffect, useCallback } from "react";
import { Search, X, Filter } from "lucide-react";
import type { Category, Account } from "@/app/types/transactions";

interface TransactionFiltersProps {
  filters: {
    search?: string;
    category_id?: number;
    date_from?: string;
    date_to?: string;
    min_amount?: string;
    max_amount?: string;
    is_uncategorized?: boolean;
  };
  categories: Category[];
  accounts: Account[];
  onFilterChange: (filters: TransactionFiltersProps["filters"]) => void;
  onClearFilters: () => void;
}

type AmountFilterType = "all" | "income" | "expense";

export function TransactionFilters({
  filters,
  categories,
  accounts,
  onFilterChange,
  onClearFilters,
}: TransactionFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search || "");
  const [isExpanded, setIsExpanded] = useState(false);
  const [amountType, setAmountType] = useState<AmountFilterType>("all");
  const [minAmountInput, setMinAmountInput] = useState("");
  const [maxAmountInput, setMaxAmountInput] = useState("");

  // Debounce search input (500ms)
  useEffect(() => {
    // Don't trigger on initial mount if search is empty
    if (searchInput === "" && filters.search === undefined) {
      return;
    }
    
    const timer = setTimeout(() => {
      if (searchInput !== filters.search) {
        onFilterChange({ ...filters, search: searchInput || undefined });
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchInput]); // Only depend on searchInput to avoid re-triggering on filter changes

  // Sync search input with filters prop (for clear filters)
  useEffect(() => {
    if (filters.search === undefined && searchInput !== "") {
      setSearchInput("");
    }
  }, [filters.search]);

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onFilterChange({
      ...filters,
      category_id: value ? Number(value) : undefined,
      is_uncategorized: undefined, // Clear uncategorized filter
    });
  };

  const handleUncategorizedChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    onFilterChange({
      ...filters,
      is_uncategorized: e.target.checked || undefined,
      category_id: undefined, // Clear category filter
    });
  };

  const handleDateFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      date_from: e.target.value || undefined,
    });
  };

  const handleDateToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      date_to: e.target.value || undefined,
    });
  };

  const handleAmountTypeChange = (type: AmountFilterType) => {
    setAmountType(type);
    setMinAmountInput("");
    setMaxAmountInput("");

    // Clear amount filters when switching type
    onFilterChange({
      ...filters,
      min_amount: undefined,
      max_amount: undefined,
    });
  };

  const handleMinAmountChange = (value: string) => {
    setMinAmountInput(value);

    if (!value) {
      onFilterChange({
        ...filters,
        min_amount: undefined,
      });
      return;
    }

    const numValue = parseFloat(value);
    if (isNaN(numValue)) return;

    // For expenses, we want to filter negative amounts
    // So min expense of 10 means amounts <= -10
    if (amountType === "expense") {
      onFilterChange({
        ...filters,
        max_amount: (-numValue).toString(),
      });
    } else if (amountType === "income") {
      onFilterChange({
        ...filters,
        min_amount: numValue.toString(),
      });
    } else {
      onFilterChange({
        ...filters,
        min_amount: value,
      });
    }
  };

  const handleMaxAmountChange = (value: string) => {
    setMaxAmountInput(value);

    if (!value) {
      onFilterChange({
        ...filters,
        max_amount: undefined,
      });
      return;
    }

    const numValue = parseFloat(value);
    if (isNaN(numValue)) return;

    // For expenses, we want to filter negative amounts
    // So max expense of 100 means amounts >= -100
    if (amountType === "expense") {
      onFilterChange({
        ...filters,
        min_amount: (-numValue).toString(),
      });
    } else if (amountType === "income") {
      onFilterChange({
        ...filters,
        max_amount: numValue.toString(),
      });
    } else {
      onFilterChange({
        ...filters,
        max_amount: value,
      });
    }
  };

  const hasActiveFilters =
    filters.search ||
    filters.category_id ||
    filters.date_from ||
    filters.date_to ||
    filters.min_amount ||
    filters.max_amount ||
    filters.is_uncategorized;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
      {/* Search Bar - Always Visible */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search transactions..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`px-4 py-2 border rounded-lg flex items-center gap-2 transition-colors ${
            isExpanded
              ? "bg-green-50 border-green-500 text-green-700"
              : "border-gray-300 text-gray-700 hover:bg-gray-50"
          }`}
        >
          <Filter className="h-5 w-5" />
          <span className="hidden sm:inline">Filters</span>
          {hasActiveFilters && !isExpanded && (
            <span className="bg-green-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
              {
                [
                  filters.category_id,
                  filters.date_from,
                  filters.date_to,
                  filters.min_amount,
                  filters.max_amount,
                  filters.is_uncategorized,
                ].filter(Boolean).length
              }
            </span>
          )}
        </button>
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="px-4 py-2 border border-gray-300 rounded-lg flex items-center gap-2 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <X className="h-5 w-5" />
            <span className="hidden sm:inline">Clear</span>
          </button>
        )}
      </div>

      {/* Expanded Filters */}
      {isExpanded && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={filters.category_id || ""}
              onChange={handleCategoryChange}
              disabled={filters.is_uncategorized}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">All categories</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          {/* Uncategorized Checkbox */}
          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.is_uncategorized || false}
                onChange={handleUncategorizedChange}
                className="h-4 w-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
              />
              <span className="text-sm font-medium text-gray-700">
                Uncategorized only
              </span>
            </label>
          </div>

          {/* Date From */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Date
            </label>
            <input
              type="date"
              value={filters.date_from || ""}
              onChange={handleDateFromChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          {/* Date To */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To Date
            </label>
            <input
              type="date"
              value={filters.date_to || ""}
              onChange={handleDateToChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          {/* Amount Filter Type */}
          <div className="sm:col-span-2 lg:col-span-3">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount Filter
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleAmountTypeChange("all")}
                className={`flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  amountType === "all"
                    ? "bg-green-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                All Transactions
              </button>
              <button
                type="button"
                onClick={() => handleAmountTypeChange("income")}
                className={`flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  amountType === "income"
                    ? "bg-green-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                Income Only
              </button>
              <button
                type="button"
                onClick={() => handleAmountTypeChange("expense")}
                className={`flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  amountType === "expense"
                    ? "bg-green-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                Expenses Only
              </button>
            </div>
          </div>

          {/* Amount Range - Only show when income or expense is selected */}
          {amountType !== "all" && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {amountType === "income" ? "Min Income" : "Min Expense"}
                </label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={minAmountInput}
                  onChange={(e) => handleMinAmountChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="mt-1 text-xs text-gray-500">
                  {amountType === "income"
                    ? "Show income greater than this amount"
                    : "Show expenses greater than this amount"}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {amountType === "income" ? "Max Income" : "Max Expense"}
                </label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={maxAmountInput}
                  onChange={(e) => handleMaxAmountChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
                <p className="mt-1 text-xs text-gray-500">
                  {amountType === "income"
                    ? "Show income less than this amount"
                    : "Show expenses less than this amount"}
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
