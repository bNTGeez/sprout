"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronUp,
  Building2,
  Plus,
  Trash2,
  RefreshCw,
} from "lucide-react";
import { Account } from "@/app/types/accounts";
import { PlaidItem, deletePlaidItem, triggerPlaidSync } from "@/lib/api";
import {
  formatCurrency,
  getAccountIcon,
  getAccountTypeLabel,
} from "@/lib/accounts";
import AccountHealthIndicator from "./AccountHealthIndicator";
import { createClient } from "@/lib/supabase/client";
import { Toast, ToastType } from "../Toast";
import { DisconnectConfirmModal } from "./DisconnectConfirmModal";

interface PlaidItemCardProps {
  plaidItem: PlaidItem;
  accounts: Account[];
  onReauth?: () => void;
  onDisconnect?: () => void;
  onAddAccounts?: () => void;
}

export default function PlaidItemCard({
  plaidItem,
  accounts,
  onReauth,
  onDisconnect,
  onAddAccounts,
}: PlaidItemCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isDisconnectModalOpen, setIsDisconnectModalOpen] = useState(false);
  const [toast, setToast] = useState<{
    type: ToastType;
    message: string;
  } | null>(null);

  // Calculate total balance: assets (positive) minus liabilities (credit cards, negative)
  const totalBalance = accounts.reduce(
    (sum, acc) => {
      const balance = parseFloat(acc.balance);
      // Credit cards are liabilities - subtract from net worth
      if (acc.account_type === "credit_card") {
        return sum - balance; // Subtract credit card balance (it's already positive from Plaid)
      }
      // All other accounts (checking, savings, etc.) are assets - add to net worth
      return sum + balance;
    },
    0
  );

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token) {
        throw new Error("Not authenticated");
      }

      const result = await triggerPlaidSync(session.access_token, plaidItem.id);
      const totalTransactions =
        result.transactions.added + result.transactions.modified;
      const totalRemoved = result.transactions.removed || 0;

      // Build a more informative message
      const parts: string[] = [];
      if (result.accounts_synced > 0) {
        parts.push(
          `${result.accounts_synced} account${
            result.accounts_synced === 1 ? "" : "s"
          } synced`
        );
      }
      if (totalTransactions > 0) {
        parts.push(
          `${totalTransactions} transaction${
            totalTransactions === 1 ? "" : "s"
          } updated`
        );
      }
      if (totalRemoved > 0) {
        parts.push(
          `${totalRemoved} transaction${totalRemoved === 1 ? "" : "s"} removed`
        );
      }

      if (parts.length === 0) {
        setToast({
          type: "info",
          message: "Sync complete! No new transactions found.",
        });
      } else {
        setToast({
          type: "success",
          message: `Sync complete! ${parts.join(", ")}.`,
        });
      }

      // Refresh the page to show new transactions after a short delay
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (error) {
      console.error("Failed to sync:", error);
      setToast({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "Failed to sync transactions",
      });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleDisconnectClick = () => {
    setIsDisconnectModalOpen(true);
  };

  const handleDisconnect = async () => {
    setIsDisconnectModalOpen(false);
    setIsDeleting(true);
    try {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session?.access_token) {
        throw new Error("Not authenticated");
      }

      await deletePlaidItem(session.access_token, plaidItem.id);
      setToast({
        type: "success",
        message: `${plaidItem.institution_name} disconnected successfully`,
      });
      if (onDisconnect) {
        // Delay callback to show toast first
        setTimeout(() => {
          onDisconnect();
        }, 1500);
      }
    } catch (error) {
      console.error("Failed to disconnect:", error);
      setToast({
        type: "error",
        message: error instanceof Error
          ? error.message
          : "Failed to disconnect institution",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <Building2 className="w-5 h-5 text-blue-600" />
          </div>
          <div className="text-left">
            <h3 className="font-semibold text-gray-900">
              {plaidItem.institution_name}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <AccountHealthIndicator
                status={plaidItem.status}
                institutionName={plaidItem.institution_name}
                onReauth={onReauth}
              />
              <span className="text-sm text-gray-400">•</span>
              <span className="text-sm text-gray-500">
                {accounts.length}{" "}
                {accounts.length === 1 ? "account" : "accounts"}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">Total Balance</p>
            <p
              className={`font-semibold font-numbers ${
                totalBalance >= 0 ? "text-green-600" : "text-red-600"
              }`}
            >
              {formatCurrency(totalBalance)}
            </p>
          </div>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </button>

      {/* Accounts List */}
      {isExpanded && (
        <div className="border-t">
          {accounts.map((account, index) => {
            const Icon = getAccountIcon(account.account_type);
            const balanceNum = parseFloat(account.balance);
            // Credit cards are liabilities - always show as negative/red for display
            const isPositive = account.account_type !== "credit_card" && balanceNum >= 0;

            return (
              <div
                key={account.id}
                className={`px-6 py-3 flex items-center justify-between ${
                  index !== accounts.length - 1 ? "border-b" : ""
                } ${!account.is_active ? "opacity-60" : ""}`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5 text-gray-500" />
                  <div>
                    <p className="font-medium text-gray-900">{account.name}</p>
                    <p className="text-xs text-gray-500">
                      {getAccountTypeLabel(account.account_type)}
                      {!account.is_active && " • Inactive"}
                    </p>
                  </div>
                </div>
                <p
                  className={`font-semibold font-numbers ${
                    isPositive ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {formatCurrency(account.balance)}
                </p>
              </div>
            );
          })}

          {/* Action Buttons */}
          <div className="px-6 py-3 border-t bg-gray-50 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={handleSync}
              disabled={isSyncing}
              className="px-3 py-1.5 text-sm font-medium text-green-600 bg-white border border-green-200 rounded-lg hover:bg-green-50 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw
                className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`}
              />
              {isSyncing ? "Syncing..." : "Sync Transactions"}
            </button>
            <button
              type="button"
              onClick={onAddAccounts}
              className="px-3 py-1.5 text-sm font-medium text-blue-600 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add More Accounts
            </button>
            <button
              type="button"
              onClick={handleDisconnect}
              disabled={isDeleting}
              className="px-3 py-1.5 text-sm font-medium text-red-600 bg-white border border-red-200 rounded-lg hover:bg-red-50 transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Trash2 className="w-4 h-4" />
              {isDeleting ? "Disconnecting..." : "Disconnect"}
            </button>
          </div>
        </div>
      )}

      {/* Disconnect Confirmation Modal */}
      <DisconnectConfirmModal
        isOpen={isDisconnectModalOpen}
        onClose={() => setIsDisconnectModalOpen(false)}
        onConfirm={handleDisconnect}
        institutionName={plaidItem.institution_name}
        isDisconnecting={isDeleting}
      />

      {/* Toast Notification */}
      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
