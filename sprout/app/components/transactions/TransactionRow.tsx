"use client";

import { useState, useEffect, useRef } from "react";
import { Pencil, Trash2, RefreshCw, Check, X } from "lucide-react";
import { CategoryBadge } from "./CategoryBadge";
import { DeleteConfirmModal } from "./DeleteConfirmModal";
import type { Transaction, Category, TransactionUpdateRequest } from "@/app/types/transactions";

interface TransactionRowProps {
  transaction: Transaction;
  categories: Category[];
  onUpdate: (id: number, data: TransactionUpdateRequest) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  onError: (message: string) => void;
}

export function TransactionRow({
  transaction,
  categories,
  onUpdate,
  onDelete,
  onError,
}: TransactionRowProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [editData, setEditData] = useState<{
    description: string;
    amount: string;
    date: string;
    category_id: number | null;
    notes: string;
  }>({
    description: transaction.description,
    amount: Math.abs(parseFloat(transaction.amount)).toString(),
    date: transaction.date,
    category_id: transaction.category_id,
    notes: transaction.notes || "",
  });

  const descriptionRef = useRef<HTMLInputElement>(null);

  // Focus description input when entering edit mode
  useEffect(() => {
    if (isEditing && descriptionRef.current) {
      descriptionRef.current.focus();
    }
  }, [isEditing]);

  // Reset edit data when transaction changes (for optimistic updates)
  useEffect(() => {
    setEditData({
      description: transaction.description,
      amount: Math.abs(parseFloat(transaction.amount)).toString(),
      date: transaction.date,
      category_id: transaction.category_id,
      notes: transaction.notes || "",
    });
  }, [transaction]);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    // Reset to original values
    setEditData({
      description: transaction.description,
      amount: Math.abs(parseFloat(transaction.amount)).toString(),
      date: transaction.date,
      category_id: transaction.category_id,
      notes: transaction.notes || "",
    });
  };

  const handleSave = async () => {
    // Validate amount first
    const amount = parseFloat(editData.amount);
    if (isNaN(amount) || amount <= 0) {
      onError("Amount must be a positive number");
      return;
    }

    if (!editData.description.trim()) {
      onError("Description is required");
      return;
    }

    setIsUpdating(true);
    try {
      const isExpense = parseFloat(transaction.amount) < 0;
      const finalAmount = isExpense ? -Math.abs(amount) : Math.abs(amount);

      const updatePayload: TransactionUpdateRequest = {};
      
      // Only include fields that have changed
      if (editData.description.trim() !== transaction.description) {
        updatePayload.description = editData.description.trim();
      }
      
      if (finalAmount.toString() !== transaction.amount) {
        updatePayload.amount = finalAmount.toString();
      }
      
      if (editData.date !== transaction.date) {
        updatePayload.date = editData.date;
      }
      
      if (editData.category_id !== transaction.category_id) {
        updatePayload.category_id = editData.category_id;
      }
      
      const newNotes = editData.notes.trim() || null;
      if (newNotes !== transaction.notes) {
        updatePayload.notes = newNotes;
      }

      await onUpdate(transaction.id, updatePayload);

      setIsEditing(false);
    } catch (error) {
      console.error("Failed to update transaction:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to update transaction. Please try again.";
      onError(errorMessage);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteClick = () => {
    setIsDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    setIsDeleting(true);
    try {
      await onDelete(transaction.id);
      setIsDeleteModalOpen(false);
    } catch (error) {
      console.error("Failed to delete transaction:", error);
      const errorMessage = error instanceof Error ? error.message : "Failed to delete transaction. Please try again.";
      onError(errorMessage);
      setIsDeleteModalOpen(false);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  const amount = parseFloat(transaction.amount);
  const isExpense = amount < 0;
  const formattedAmount = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    signDisplay: "never",
  }).format(Math.abs(amount));

  const formattedDate = new Date(transaction.date).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  if (isEditing) {
    return (
      <tr className="bg-blue-50">
        {/* Date */}
        <td className="px-6 py-4 whitespace-nowrap">
          <input
            type="date"
            value={editData.date}
            onChange={(e) => setEditData({ ...editData, date: e.target.value })}
            onKeyDown={handleKeyDown}
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isUpdating}
          />
        </td>

        {/* Description */}
        <td className="px-6 py-4">
          <div className="space-y-2">
            <input
              ref={descriptionRef}
              type="text"
              value={editData.description}
              onChange={(e) =>
                setEditData({ ...editData, description: e.target.value })
              }
              onKeyDown={handleKeyDown}
              placeholder="Description"
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isUpdating}
            />
            <input
              type="text"
              value={editData.notes}
              onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
              onKeyDown={handleKeyDown}
              placeholder="Notes (optional)"
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isUpdating}
            />
          </div>
        </td>

        {/* Category */}
        <td className="px-6 py-4 whitespace-nowrap">
          <select
            value={editData.category_id || ""}
            onChange={(e) =>
              setEditData({
                ...editData,
                category_id: e.target.value ? parseInt(e.target.value) : null,
              })
            }
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isUpdating}
          >
            <option value="">Uncategorized</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.icon} {cat.name}
              </option>
            ))}
          </select>
        </td>

        {/* Account (read-only) */}
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          {transaction.account.name}
        </td>

        {/* Amount */}
        <td className="px-6 py-4 whitespace-nowrap text-right">
          <div className="flex items-center justify-end gap-1">
            <span className={`text-sm font-semibold ${isExpense ? "text-red-600" : "text-green-600"}`}>
              {isExpense ? "-$" : "+$"}
            </span>
            <input
              type="number"
              step="0.01"
              value={editData.amount}
              onChange={(e) => setEditData({ ...editData, amount: e.target.value })}
              onKeyDown={handleKeyDown}
              placeholder="0.00"
              className="w-24 px-2 py-1 text-sm text-right border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isUpdating}
            />
          </div>
        </td>

        {/* Actions */}
        <td className="px-6 py-4 whitespace-nowrap text-right">
          <div className="flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={handleSave}
              disabled={isUpdating}
              className="text-green-600 hover:text-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Save changes"
            >
              {isUpdating ? (
                <div className="h-4 w-4 border-2 border-green-600 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Check className="w-4 h-4" />
              )}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              disabled={isUpdating}
              className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Cancel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </td>
      </tr>
    );
  }

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      {/* Date */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {formattedDate}
      </td>

      {/* Description / Merchant */}
      <td className="px-6 py-4">
        <div className="flex flex-col">
          <span className="text-sm font-medium text-gray-900">
            {transaction.description}
          </span>
          {transaction.normalized_merchant && (
            <span className="text-xs text-gray-500 mt-0.5">
              {transaction.normalized_merchant}
            </span>
          )}
          {transaction.notes && (
            <span className="text-xs text-gray-500 mt-0.5 italic">
              Note: {transaction.notes}
            </span>
          )}
          {transaction.is_subscription && (
            <span className="inline-flex items-center gap-1 text-xs text-purple-600 mt-1">
              <RefreshCw className="w-3 h-3" />
              Recurring
            </span>
          )}
        </div>
      </td>

      {/* Category */}
      <td className="px-6 py-4 whitespace-nowrap">
        <CategoryBadge category={transaction.category} />
      </td>

      {/* Account */}
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {transaction.account.name}
      </td>

      {/* Amount */}
      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-right">
        <span className={isExpense ? "text-red-600" : "text-green-600"}>
          {isExpense ? "-" : "+"}
          {formattedAmount}
        </span>
      </td>

      {/* Actions */}
      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={handleEdit}
            className="text-gray-400 hover:text-blue-600 transition-colors"
            title="Edit transaction"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={handleDeleteClick}
            className="text-gray-400 hover:text-red-600 transition-colors"
            title="Delete transaction"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </td>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDeleteConfirm}
        transactionDescription={transaction.description}
        isDeleting={isDeleting}
      />
    </tr>
  );
}
