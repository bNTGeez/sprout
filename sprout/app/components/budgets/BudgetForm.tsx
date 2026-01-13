"use client";

import { useState, useEffect } from "react";
import { X, DollarSign, Calendar, Tag } from "lucide-react";
import type { Category } from "@/app/types/transactions";
import type {
  Budget,
  BudgetCreateRequest,
  BudgetUpdateRequest,
} from "@/app/types/budgets";

interface BudgetFormProps {
  isOpen: boolean;
  onClose: () => void;
  categories: Category[];
  budget?: Budget | null; // If provided, we're editing; otherwise creating
  defaultMonth?: number; // Default month when creating (defaults to current month)
  defaultYear?: number; // Default year when creating (defaults to current year)
  onSubmit: (data: BudgetCreateRequest | BudgetUpdateRequest) => Promise<void>;
}

interface FormErrors {
  category_id?: string;
  amount?: string;
  month?: string;
  year?: string;
}

export function BudgetForm({
  isOpen,
  onClose,
  categories,
  budget,
  defaultMonth,
  defaultYear,
  onSubmit,
}: BudgetFormProps) {
  const today = new Date();
  const currentMonth = today.getMonth() + 1;
  const currentYear = today.getFullYear();

  // Use provided defaults or fall back to current month/year
  const initialMonth = defaultMonth ?? currentMonth;
  const initialYear = defaultYear ?? currentYear;

  const [formData, setFormData] = useState({
    category_id: budget?.category_id || 0,
    month: budget?.month || initialMonth,
    year: budget?.year || initialYear,
    amount: budget?.amount || "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset form when modal opens or budget changes
  useEffect(() => {
    if (isOpen) {
      if (budget) {
        // Editing existing budget
        setFormData({
          category_id: budget.category_id,
          month: budget.month,
          year: budget.year,
          amount: budget.amount,
        });
      } else {
        // Creating new budget - use provided defaults or current month/year
        setFormData({
          category_id: 0,
          month: defaultMonth ?? currentMonth,
          year: defaultYear ?? currentYear,
          amount: "",
        });
      }
      setErrors({});
    }
  }, [isOpen, budget, defaultMonth, defaultYear, currentMonth, currentYear]);

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

    if (!formData.category_id || formData.category_id === 0) {
      newErrors.category_id = "Please select a category";
    }

    if (!formData.amount || formData.amount === "") {
      newErrors.amount = "Amount is required";
    } else {
      const amount = parseFloat(formData.amount);
      if (isNaN(amount) || amount <= 0) {
        newErrors.amount = "Amount must be greater than 0";
      }
    }

    if (formData.month < 1 || formData.month > 12) {
      newErrors.month = "Month must be between 1 and 12";
    }

    if (formData.year < 2000 || formData.year > 2100) {
      newErrors.year = "Year must be between 2000 and 2100";
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
      if (budget) {
        // Update existing budget (only amount can be updated per backend API)
        await onSubmit({
          amount: formData.amount,
        });
      } else {
        // Create new budget
        await onSubmit({
          category_id: formData.category_id,
          month: formData.month,
          year: formData.year,
          amount: formData.amount,
        });
      }

      onClose();
    } catch (error) {
      console.error("Failed to save budget:", error);
      // Error will be handled by parent component (toast)
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const isEditMode = !!budget;

  return (
    <>
      {/* Backdrop */}
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
          className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">
              {isEditMode ? "Edit Budget" : "Add Budget"}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Category */}
            <div>
              <label
                htmlFor="category_id"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Category <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Tag className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <select
                  id="category_id"
                  value={formData.category_id}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      category_id: parseInt(e.target.value),
                    })
                  }
                  disabled={isEditMode} // Can't change category when editing
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.category_id ? "border-red-500" : "border-gray-300"
                  } ${isEditMode ? "bg-gray-100 cursor-not-allowed" : ""}`}
                >
                  <option value={0}>Select a category</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>
              {errors.category_id && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.category_id}
                </p>
              )}
            </div>

            {/* Month and Year */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="month"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Month <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <select
                    id="month"
                    value={formData.month}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        month: parseInt(e.target.value),
                      })
                    }
                    disabled={isEditMode} // Can't change month/year when editing
                    className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                      errors.month ? "border-red-500" : "border-gray-300"
                    } ${isEditMode ? "bg-gray-100 cursor-not-allowed" : ""}`}
                  >
                    {Array.from({ length: 12 }, (_, i) => i + 1).map(
                      (month) => (
                        <option key={month} value={month}>
                          {new Date(2000, month - 1).toLocaleDateString(
                            "en-US",
                            {
                              month: "long",
                            }
                          )}
                        </option>
                      )
                    )}
                  </select>
                </div>
                {errors.month && (
                  <p className="mt-1 text-sm text-red-600">{errors.month}</p>
                )}
              </div>

              <div>
                <label
                  htmlFor="year"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Year <span className="text-red-500">*</span>
                </label>
                <input
                  id="year"
                  type="number"
                  min="2000"
                  max="2100"
                  value={formData.year}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      year: parseInt(e.target.value),
                    })
                  }
                  disabled={isEditMode}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.year ? "border-red-500" : "border-gray-300"
                  } ${isEditMode ? "bg-gray-100 cursor-not-allowed" : ""}`}
                />
                {errors.year && (
                  <p className="mt-1 text-sm text-red-600">{errors.year}</p>
                )}
              </div>
            </div>

            {/* Amount */}
            <div>
              <label
                htmlFor="amount"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Budget Amount <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  value={formData.amount}
                  onChange={(e) =>
                    setFormData({ ...formData, amount: e.target.value })
                  }
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.amount ? "border-red-500" : "border-gray-300"
                  }`}
                />
              </div>
              {errors.amount && (
                <p className="mt-1 text-sm text-red-600">{errors.amount}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Enter the maximum amount you want to spend in this category for
                the selected month
              </p>
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
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    {isEditMode ? "Saving..." : "Creating..."}
                  </>
                ) : isEditMode ? (
                  "Save Changes"
                ) : (
                  "Create Budget"
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
