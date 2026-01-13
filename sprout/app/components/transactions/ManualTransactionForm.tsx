"use client";

import { useState, useEffect } from "react";
import {
  X,
  DollarSign,
  Calendar,
  FileText,
  Tag,
  Target,
  Store,
} from "lucide-react";
import type {
  Category,
  Account,
  TransactionCreateRequest,
} from "@/app/types/transactions";
import type { Goal } from "@/app/types/goals";

interface ManualTransactionFormProps {
  isOpen: boolean;
  onClose: () => void;
  categories: Category[];
  accounts: Account[];
  goals: Goal[];
  onSubmit: (transaction: TransactionCreateRequest) => Promise<void>;
}

interface FormErrors {
  account_id?: string;
  amount?: string;
  date?: string;
  description?: string;
}

export function ManualTransactionForm({
  isOpen,
  onClose,
  categories,
  accounts,
  goals,
  onSubmit,
}: ManualTransactionFormProps) {
  const [formData, setFormData] = useState<TransactionCreateRequest>({
    account_id: 0,
    amount: "",
    date: new Date().toISOString().split("T")[0], // Today's date
    description: "",
    category_id: null,
    goal_id: null,
    notes: null,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [transactionType, setTransactionType] = useState<"expense" | "income">(
    "expense"
  );

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        account_id: accounts.length > 0 ? accounts[0].id : 0,
        amount: "",
        date: new Date().toISOString().split("T")[0],
        description: "",
        category_id: null,
        goal_id: null,
        notes: null,
        normalized_merchant: null,
      });
      setErrors({});
      setTransactionType("expense");
    }
  }, [isOpen, accounts]);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isOpen, onClose]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.account_id || formData.account_id === 0) {
      newErrors.account_id = "Please select an account";
    }

    if (!formData.amount || formData.amount === "") {
      newErrors.amount = "Amount is required";
    } else {
      const amount = parseFloat(formData.amount);
      if (isNaN(amount) || amount <= 0) {
        newErrors.amount = "Amount must be a positive number";
      }
    }

    if (!formData.date) {
      newErrors.date = "Date is required";
    }

    if (!formData.description || formData.description.trim() === "") {
      newErrors.description = "Description is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Convert amount to negative for expenses
      const amount = parseFloat(formData.amount);
      const finalAmount =
        transactionType === "expense" ? -Math.abs(amount) : Math.abs(amount);

      await onSubmit({
        ...formData,
        amount: finalAmount.toString(),
        category_id: formData.category_id || null,
        notes: formData.notes?.trim() || null,
        normalized_merchant: formData.normalized_merchant?.trim() || null,
      });

      // Success - form will be reset by useEffect when modal reopens
      onClose();
    } catch (error) {
      console.error("Failed to create transaction:", error);
      // Error will be handled by parent component (toast)
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const hasNoAccounts = accounts.length === 0;

  return (
    <>
      {/* Backdrop with blur */}
      <div
        className="fixed inset-0 backdrop-blur-sm bg-white/30 z-40 transition-all"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <div
          className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">
              Add Transaction
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* No Accounts Warning */}
          {hasNoAccounts && (
            <div className="mx-6 mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-5 h-5 text-yellow-600">⚠️</div>
                <div>
                  <h3 className="text-sm font-semibold text-yellow-800">
                    No Accounts Available
                  </h3>
                  <p className="mt-1 text-sm text-yellow-700">
                    You need to connect a bank account or create a manual
                    account before adding transactions. Please connect your bank
                    using Plaid or contact support to set up manual accounts.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Transaction Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Transaction Type
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setTransactionType("expense")}
                  className={`px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                    transactionType === "expense"
                      ? "bg-red-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Expense
                </button>
                <button
                  type="button"
                  onClick={() => setTransactionType("income")}
                  className={`px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                    transactionType === "income"
                      ? "bg-green-600 text-white"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}
                >
                  Income
                </button>
              </div>
            </div>

            {/* Account */}
            <div>
              <label
                htmlFor="account_id"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Account <span className="text-red-500">*</span>
              </label>
              <select
                id="account_id"
                value={formData.account_id}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    account_id: parseInt(e.target.value),
                  })
                }
                disabled={hasNoAccounts}
                className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                  errors.account_id ? "border-red-500" : "border-gray-300"
                } ${hasNoAccounts ? "bg-gray-100 cursor-not-allowed" : ""}`}
              >
                <option value={0}>
                  {hasNoAccounts
                    ? "No accounts available"
                    : "Select an account"}
                </option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name} ({account.account_type})
                  </option>
                ))}
              </select>
              {errors.account_id && (
                <p className="mt-1 text-sm text-red-600">{errors.account_id}</p>
              )}
            </div>

            {/* Amount */}
            <div>
              <label
                htmlFor="amount"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Amount <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="amount"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.amount}
                  onChange={(e) =>
                    setFormData({ ...formData, amount: e.target.value })
                  }
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                    errors.amount ? "border-red-500" : "border-gray-300"
                  }`}
                />
              </div>
              {errors.amount && (
                <p className="mt-1 text-sm text-red-600">{errors.amount}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Enter as positive number (e.g., 50.00)
              </p>
            </div>

            {/* Date */}
            <div>
              <label
                htmlFor="date"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Date <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="date"
                  type="date"
                  value={formData.date}
                  onChange={(e) =>
                    setFormData({ ...formData, date: e.target.value })
                  }
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                    errors.date ? "border-red-500" : "border-gray-300"
                  }`}
                />
              </div>
              {errors.date && (
                <p className="mt-1 text-sm text-red-600">{errors.date}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Description <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <FileText className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="description"
                  type="text"
                  placeholder="e.g., Grocery shopping at Whole Foods"
                  value={formData.description}
                  onChange={(e) =>
                    setFormData({ ...formData, description: e.target.value })
                  }
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent ${
                    errors.description ? "border-red-500" : "border-gray-300"
                  }`}
                />
              </div>
              {errors.description && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.description}
                </p>
              )}
            </div>

            {/* Merchant */}
            <div>
              <label
                htmlFor="normalized_merchant"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Merchant (optional)
              </label>
              <div className="relative">
                <Store className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="normalized_merchant"
                  type="text"
                  placeholder="e.g., Whole Foods, Starbucks, Amazon"
                  value={formData.normalized_merchant || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      normalized_merchant: e.target.value.trim() || null,
                    })
                  }
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                />
              </div>
              <p className="mt-1 text-xs text-gray-500">
                The merchant or business name for this transaction
              </p>
            </div>

            {/* Category */}
            <div>
              <label
                htmlFor="category_id"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Category
              </label>
              <div className="relative">
                <Tag className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <select
                  id="category_id"
                  value={formData.category_id || ""}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      category_id: e.target.value
                        ? parseInt(e.target.value)
                        : null,
                    })
                  }
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                >
                  <option value="">No category (uncategorized)</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Goal (only show for income transactions) */}
            {transactionType === "income" && (
              <div>
                <label
                  htmlFor="goal_id"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Goal (optional)
                </label>
                <div className="relative">
                  <Target className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
                  <select
                    id="goal_id"
                    value={formData.goal_id || ""}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        goal_id: e.target.value
                          ? parseInt(e.target.value)
                          : null,
                      })
                    }
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="">No goal</option>
                    {goals.map((goal) => (
                      <option key={goal.id} value={goal.id}>
                        {goal.name}
                      </option>
                    ))}
                  </select>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Link this income to a savings goal
                </p>
              </div>
            )}

            {/* Notes */}
            <div>
              <label
                htmlFor="notes"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Notes
              </label>
              <textarea
                id="notes"
                rows={3}
                placeholder="Additional notes (optional)"
                value={formData.notes || ""}
                onChange={(e) =>
                  setFormData({ ...formData, notes: e.target.value })
                }
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
              />
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || hasNoAccounts}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Add Transaction"
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
