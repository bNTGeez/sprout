"use client";

import { useState, useEffect } from "react";
import { X, DollarSign, Calendar, Target, Archive } from "lucide-react";
import type {
  Goal,
  GoalCreateRequest,
  GoalUpdateRequest,
} from "@/app/types/goals";

interface GoalFormProps {
  isOpen: boolean;
  onClose: () => void;
  goal?: Goal | null; // If provided, we're editing; otherwise creating
  onSubmit: (data: GoalCreateRequest | GoalUpdateRequest) => Promise<void>;
}

interface FormErrors {
  name?: string;
  target_amount?: string;
  target_date?: string;
  monthly_contribution?: string;
}

export function GoalForm({ isOpen, onClose, goal, onSubmit }: GoalFormProps) {
  const [formData, setFormData] = useState({
    name: goal?.name || "",
    target_amount: goal?.target_amount || "",
    target_date: goal?.target_date || "",
    monthly_contribution: goal?.monthly_contribution || "",
    is_active: goal?.is_active ?? true,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Reset form when modal opens or goal changes
  useEffect(() => {
    if (isOpen) {
      if (goal) {
        // Editing existing goal
        setFormData({
          name: goal.name,
          target_amount: goal.target_amount,
          target_date: goal.target_date || "",
          monthly_contribution: goal.monthly_contribution || "",
          is_active: goal.is_active,
        });
      } else {
        // Creating new goal
        setFormData({
          name: "",
          target_amount: "",
          target_date: "",
          monthly_contribution: "",
          is_active: true,
        });
      }
      setErrors({});
    }
  }, [isOpen, goal]);

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

    if (!formData.name || formData.name.trim() === "") {
      newErrors.name = "Goal name is required";
    }

    if (!formData.target_amount || formData.target_amount === "") {
      newErrors.target_amount = "Target amount is required";
    } else {
      const amount = parseFloat(formData.target_amount);
      if (isNaN(amount) || amount <= 0) {
        newErrors.target_amount = "Target amount must be greater than 0";
      }
    }

    if (formData.target_date) {
      const date = new Date(formData.target_date);
      if (isNaN(date.getTime())) {
        newErrors.target_date = "Invalid date format";
      }
    }

    if (formData.monthly_contribution) {
      const contribution = parseFloat(formData.monthly_contribution);
      if (isNaN(contribution) || contribution <= 0) {
        newErrors.monthly_contribution =
          "Monthly contribution must be greater than 0";
      }
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
      if (goal) {
        // Update existing goal
        const updateData: GoalUpdateRequest = {
          name: formData.name.trim(),
          target_amount: formData.target_amount,
        };

        // Only include optional fields if they have values
        if (formData.target_date) {
          updateData.target_date = formData.target_date;
        } else {
          updateData.target_date = null;
        }

        if (formData.monthly_contribution) {
          updateData.monthly_contribution = formData.monthly_contribution;
        } else {
          updateData.monthly_contribution = null;
        }

        // Include is_active in update (for archiving)
        updateData.is_active = formData.is_active;

        await onSubmit(updateData);
      } else {
        // Create new goal
        const createData: GoalCreateRequest = {
          name: formData.name.trim(),
          target_amount: formData.target_amount,
          target_date: formData.target_date || undefined,
          monthly_contribution: formData.monthly_contribution || undefined,
        };

        await onSubmit(createData);
      }

      onClose();
    } catch (error) {
      console.error("Failed to save goal:", error);
      // Error will be handled by parent component (toast)
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const isEditMode = !!goal;

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
              {isEditMode ? "Edit Goal" : "Add Goal"}
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
            {/* Goal Name */}
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Goal Name <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <Target className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="name"
                  type="text"
                  placeholder="e.g., Emergency Fund"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.name ? "border-red-500" : "border-gray-300"
                  }`}
                />
              </div>
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
            </div>

            {/* Target Amount */}
            <div>
              <label
                htmlFor="target_amount"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Target Amount <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="target_amount"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  value={formData.target_amount}
                  onChange={(e) =>
                    setFormData({ ...formData, target_amount: e.target.value })
                  }
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.target_amount ? "border-red-500" : "border-gray-300"
                  }`}
                />
              </div>
              {errors.target_amount && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.target_amount}
                </p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                The total amount you want to save
              </p>
            </div>

            {/* Target Date (Optional) */}
            <div>
              <label
                htmlFor="target_date"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Target Date (Optional)
              </label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="target_date"
                  type="date"
                  value={formData.target_date}
                  onChange={(e) =>
                    setFormData({ ...formData, target_date: e.target.value })
                  }
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.target_date ? "border-red-500" : "border-gray-300"
                  }`}
                />
              </div>
              {errors.target_date && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.target_date}
                </p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                When you want to reach this goal (optional)
              </p>
            </div>

            {/* Monthly Contribution (Optional) */}
            <div>
              <label
                htmlFor="monthly_contribution"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Monthly Contribution (Optional)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  id="monthly_contribution"
                  type="number"
                  step="0.01"
                  min="0.01"
                  placeholder="0.00"
                  value={formData.monthly_contribution}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      monthly_contribution: e.target.value,
                    })
                  }
                  className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.monthly_contribution
                      ? "border-red-500"
                      : "border-gray-300"
                  }`}
                />
              </div>
              {errors.monthly_contribution && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.monthly_contribution}
                </p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                How much you plan to contribute each month (optional)
              </p>
            </div>

            {/* Archive Option (only when editing) */}
            {isEditMode && (
              <div className="pt-4 border-t border-gray-200">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={!formData.is_active}
                    onChange={(e) =>
                      setFormData({ ...formData, is_active: !e.target.checked })
                    }
                    className="w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500"
                  />
                  <div className="flex items-center gap-2">
                    <Archive className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">
                      Archive this goal
                    </span>
                  </div>
                </label>
                <p className="mt-1 ml-7 text-xs text-gray-500">
                  Archived goals are hidden from your active goals list but
                  remain in your account for reference.
                </p>
              </div>
            )}

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
                  "Create Goal"
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  );
}
