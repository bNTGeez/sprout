"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Building2, AlertCircle, CheckCircle } from "lucide-react";
import { Account } from "@/app/types/accounts";
import { PlaidItem } from "@/lib/api";
import { formatCurrency, getAccountIcon, getAccountTypeLabel } from "@/lib/accounts";

interface PlaidItemCardProps {
  plaidItem: PlaidItem;
  accounts: Account[];
}

export default function PlaidItemCard({ plaidItem, accounts }: PlaidItemCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const totalBalance = accounts.reduce(
    (sum, acc) => sum + parseFloat(acc.balance),
    0
  );

  const getStatusIcon = () => {
    switch (plaidItem.status) {
      case "good":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "error":
      case "requires_reauth":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Building2 className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (plaidItem.status) {
      case "good":
        return "Connected";
      case "error":
        return "Error";
      case "requires_reauth":
        return "Needs Reauth";
      default:
        return plaidItem.status;
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
              {getStatusIcon()}
              <span className="text-sm text-gray-500">{getStatusText()}</span>
              <span className="text-sm text-gray-400">•</span>
              <span className="text-sm text-gray-500">
                {accounts.length} {accounts.length === 1 ? "account" : "accounts"}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">Total Balance</p>
            <p className={`font-semibold ${totalBalance >= 0 ? "text-green-600" : "text-red-600"}`}>
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
            const isPositive = balanceNum >= 0;

            return (
              <div
                key={account.id}
                className={`px-6 py-3 flex items-center justify-between ${
                  index !== accounts.length - 1 ? "border-b" : ""
                } ${!account.is_active ? "opacity-60" : ""}`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`p-1.5 rounded ${
                      isPositive
                        ? "bg-green-50 text-green-600"
                        : "bg-red-50 text-red-600"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{account.name}</p>
                    <p className="text-xs text-gray-500">
                      {getAccountTypeLabel(account.account_type)}
                      {!account.is_active && " • Inactive"}
                    </p>
                  </div>
                </div>
                <p
                  className={`font-semibold ${
                    isPositive ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {formatCurrency(account.balance)}
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
