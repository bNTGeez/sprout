"use client";

import { useState, useEffect } from "react";
import { TransactionRow } from "./TransactionRow";
import { EmptyTransactionState } from "./EmptyTransactionState";
import { TransactionTableSkeleton } from "./TransactionTableSkeleton";
import { TransactionError } from "./TransactionError";
import { TransactionPagination } from "./TransactionPagination";
import { fetchTransactions } from "@/lib/api";
import type { Transaction, TransactionFilters } from "@/app/types/transactions";

// Mock data for initial implementation
const MOCK_TRANSACTIONS = [
  {
    id: 1,
    description: "Starbucks Coffee",
    amount: "-5.75",
    date: "2026-01-08",
    normalized_merchant: "Starbucks",
    category: {
      id: 1,
      name: "Dining",
      icon: "🍽️",
      color: "#FF5733",
    },
    account: {
      id: 1,
      name: "Chase Checking",
      account_type: "checking",
    },
    notes: null,
    is_subscription: false,
  },
  {
    id: 2,
    description: "Grocery Store",
    amount: "-87.32",
    date: "2026-01-07",
    normalized_merchant: "Whole Foods",
    category: {
      id: 2,
      name: "Groceries",
      icon: "🛒",
      color: "#33FF57",
    },
    account: {
      id: 2,
      name: "Chase Credit Card",
      account_type: "credit",
    },
    notes: "Weekly shopping",
    is_subscription: false,
  },
  {
    id: 3,
    description: "Netflix Subscription",
    amount: "-15.99",
    date: "2026-01-06",
    normalized_merchant: "Netflix",
    category: {
      id: 3,
      name: "Entertainment",
      icon: "🎬",
      color: "#FF33A1",
    },
    account: {
      id: 2,
      name: "Chase Credit Card",
      account_type: "credit",
    },
    notes: null,
    is_subscription: true,
  },
  {
    id: 4,
    description: "Paycheck Deposit",
    amount: "3000.00",
    date: "2026-01-05",
    normalized_merchant: "Employer",
    category: {
      id: 4,
      name: "Income",
      icon: "💰",
      color: "#4CAF50",
    },
    account: {
      id: 1,
      name: "Chase Checking",
      account_type: "checking",
    },
    notes: null,
    is_subscription: false,
  },
  {
    id: 5,
    description: "Gas Station",
    amount: "-45.00",
    date: "2026-01-04",
    normalized_merchant: "Shell",
    category: {
      id: 5,
      name: "Transportation",
      icon: "🚗",
      color: "#FF9800",
    },
    account: {
      id: 2,
      name: "Chase Credit Card",
      account_type: "credit",
    },
    notes: null,
    is_subscription: false,
  },
  {
    id: 6,
    description: "Amazon Purchase",
    amount: "-129.99",
    date: "2026-01-03",
    normalized_merchant: "Amazon",
    category: null,
    account: {
      id: 2,
      name: "Chase Credit Card",
      account_type: "credit",
    },
    notes: null,
    is_subscription: false,
  },
  {
    id: 7,
    description: "Rent Payment",
    amount: "-1500.00",
    date: "2026-01-01",
    normalized_merchant: null,
    category: {
      id: 6,
      name: "Housing",
      icon: "🏠",
      color: "#2196F3",
    },
    account: {
      id: 1,
      name: "Chase Checking",
      account_type: "checking",
    },
    notes: "Monthly rent",
    is_subscription: true,
  },
  {
    id: 8,
    description: "Restaurant",
    amount: "-67.50",
    date: "2025-12-31",
    normalized_merchant: "Olive Garden",
    category: {
      id: 1,
      name: "Dining",
      icon: "🍽️",
      color: "#FF5733",
    },
    account: {
      id: 2,
      name: "Chase Credit Card",
      account_type: "credit",
    },
    notes: "Dinner with friends",
    is_subscription: false,
  },
  {
    id: 9,
    description: "Gym Membership",
    amount: "-49.99",
    date: "2025-12-30",
    normalized_merchant: "Planet Fitness",
    category: {
      id: 7,
      name: "Health",
      icon: "💪",
      color: "#E91E63",
    },
    account: {
      id: 2,
      name: "Chase Credit Card",
      account_type: "credit",
    },
    notes: null,
    is_subscription: true,
  },
  {
    id: 10,
    description: "Coffee Shop",
    amount: "-4.50",
    date: "2025-12-29",
    normalized_merchant: "Local Cafe",
    category: {
      id: 1,
      name: "Dining",
      icon: "🍽️",
      color: "#FF5733",
    },
    account: {
      id: 1,
      name: "Chase Checking",
      account_type: "checking",
    },
    notes: null,
    is_subscription: false,
  },
];

interface TransactionTableProps {
  token: string;
  filters?: TransactionFilters;
  onPageChange?: (page: number) => void;
}

export function TransactionTable({
  token,
  filters,
  onPageChange,
}: TransactionTableProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    pages: 1,
  });

  const loadTransactions = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchTransactions(token, filters);
      setTransactions(data.transactions);
      setPagination({
        total: data.total,
        page: data.page,
        pages: data.pages,
      });

      // If current page exceeds total pages, notify parent to redirect
      if (data.page > data.pages && data.pages > 0 && onPageChange) {
        onPageChange(data.pages);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err : new Error("Failed to load transactions")
      );
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, [token, filters]);

  if (isLoading) {
    return <TransactionTableSkeleton />;
  }

  if (error) {
    return <TransactionError error={error} onRetry={loadTransactions} />;
  }

  const isEmpty = transactions.length === 0;

  if (isEmpty) {
    return (
      <div className="bg-white rounded-lg shadow">
        <EmptyTransactionState />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Date
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Description
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Category
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Account
              </th>
              <th
                scope="col"
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                Amount
              </th>
              <th scope="col" className="relative px-6 py-3">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {transactions.map((transaction) => (
              <TransactionRow key={transaction.id} transaction={transaction} />
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <TransactionPagination
        currentPage={pagination.page}
        totalPages={pagination.pages}
        totalItems={pagination.total}
        onPageChange={(page) => {
          if (onPageChange) {
            onPageChange(page);
          }
        }}
      />
    </div>
  );
}
