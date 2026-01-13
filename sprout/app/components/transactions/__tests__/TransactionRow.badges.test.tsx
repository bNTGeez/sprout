import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { TransactionRow } from "../TransactionRow";
import type { Transaction, Category } from "@/app/types/transactions";
import type { Budget } from "@/app/types/budgets";

// Mock the update/delete functions
const mockOnUpdate = vi.fn();
const mockOnDelete = vi.fn();
const mockOnError = vi.fn();

const mockCategories: Category[] = [
  { id: 1, name: "Dining", icon: "🍽️", color: "#FF5733" },
];

const mockBudget: Budget = {
  id: 1,
  user_id: 1,
  category_id: 1,
  month: 1,
  year: 2026,
  amount: "500.00",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  category: {
    id: 1,
    name: "Dining",
    icon: "🍽️",
    color: "#FF5733",
  },
  spent: "200.00",
  remaining: "300.00",
  percent_used: 40.0,
  is_over_budget: false,
};

describe("TransactionRow - Budget and Goal Badges", () => {
  it("shows budget badge for expense transactions with category", () => {
    const transaction: Transaction = {
      id: 1,
      user_id: 1,
      account_id: 1,
      category_id: 1,
      goal_id: null,
      amount: "-100.00",
      date: "2026-01-15",
      description: "Dinner",
      normalized_merchant: null,
      is_subscription: false,
      tags: null,
      notes: null,
      created_at: "2026-01-15T00:00:00Z",
      updated_at: "2026-01-15T00:00:00Z",
      category: mockCategories[0],
      account: { id: 1, name: "Checking", account_type: "checking" },
      goal: null,
    };

    const budgetMap = new Map<number, Budget>([[1, mockBudget]]);

    render(
      <TransactionRow
        transaction={transaction}
        categories={mockCategories}
        budgetMap={budgetMap}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onError={mockOnError}
      />
    );

    // Should show budget badge
    expect(screen.getByText(/300.00/)).toBeInTheDocument();
    expect(screen.getByText(/left/)).toBeInTheDocument();
  });

  it("does not show budget badge for income transactions", () => {
    const transaction: Transaction = {
      id: 2,
      user_id: 1,
      account_id: 1,
      category_id: 1,
      goal_id: null,
      amount: "100.00", // Positive = income
      date: "2026-01-15",
      description: "Salary",
      normalized_merchant: null,
      is_subscription: false,
      tags: null,
      notes: null,
      created_at: "2026-01-15T00:00:00Z",
      updated_at: "2026-01-15T00:00:00Z",
      category: mockCategories[0],
      account: { id: 1, name: "Checking", account_type: "checking" },
      goal: null,
    };

    const budgetMap = new Map<number, Budget>([[1, mockBudget]]);

    render(
      <TransactionRow
        transaction={transaction}
        categories={mockCategories}
        budgetMap={budgetMap}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onError={mockOnError}
      />
    );

    // Should NOT show budget badge for income
    expect(screen.queryByText(/left/)).not.toBeInTheDocument();
  });

  it("does not show budget badge when no category", () => {
    const transaction: Transaction = {
      id: 3,
      user_id: 1,
      account_id: 1,
      category_id: null,
      goal_id: null,
      amount: "-50.00",
      date: "2026-01-15",
      description: "Uncategorized",
      normalized_merchant: null,
      is_subscription: false,
      tags: null,
      notes: null,
      created_at: "2026-01-15T00:00:00Z",
      updated_at: "2026-01-15T00:00:00Z",
      category: null,
      account: { id: 1, name: "Checking", account_type: "checking" },
      goal: null,
    };

    const budgetMap = new Map<number, Budget>([[1, mockBudget]]);

    render(
      <TransactionRow
        transaction={transaction}
        categories={mockCategories}
        budgetMap={budgetMap}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onError={mockOnError}
      />
    );

    // Should NOT show budget badge when no category
    expect(screen.queryByText(/left/)).not.toBeInTheDocument();
  });

  it("shows goal badge when transaction is linked to a goal", () => {
    const transaction: Transaction = {
      id: 4,
      user_id: 1,
      account_id: 1,
      category_id: null,
      goal_id: 1,
      amount: "500.00",
      date: "2026-01-15",
      description: "Savings deposit",
      normalized_merchant: null,
      is_subscription: false,
      tags: null,
      notes: null,
      created_at: "2026-01-15T00:00:00Z",
      updated_at: "2026-01-15T00:00:00Z",
      category: null,
      account: { id: 1, name: "Checking", account_type: "checking" },
      goal: { id: 1, name: "Emergency Fund" },
    };

    const budgetMap = new Map<number, Budget>();

    render(
      <TransactionRow
        transaction={transaction}
        categories={mockCategories}
        budgetMap={budgetMap}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onError={mockOnError}
      />
    );

    // Should show goal badge (text may be split across elements, so use regex)
    expect(screen.getByText(/Emergency Fund/)).toBeInTheDocument();
  });

  it("shows both budget and goal badges when applicable", () => {
    const transaction: Transaction = {
      id: 5,
      user_id: 1,
      account_id: 1,
      category_id: 1,
      goal_id: 1,
      amount: "-100.00",
      date: "2026-01-15",
      description: "Expense with goal",
      normalized_merchant: null,
      is_subscription: false,
      tags: null,
      notes: null,
      created_at: "2026-01-15T00:00:00Z",
      updated_at: "2026-01-15T00:00:00Z",
      category: mockCategories[0],
      account: { id: 1, name: "Checking", account_type: "checking" },
      goal: { id: 1, name: "Emergency Fund" },
    };

    const budgetMap = new Map<number, Budget>([[1, mockBudget]]);

    render(
      <TransactionRow
        transaction={transaction}
        categories={mockCategories}
        budgetMap={budgetMap}
        onUpdate={mockOnUpdate}
        onDelete={mockOnDelete}
        onError={mockOnError}
      />
    );

    // Should show both badges
    expect(screen.getByText(/300.00/)).toBeInTheDocument(); // Budget
    expect(screen.getByText(/Emergency Fund/)).toBeInTheDocument(); // Goal (text may be split)
  });
});
