import { describe, it, expect } from "vitest";
import type { Budget } from "@/app/types/budgets";

/**
 * Test that budgetMap is built correctly from budgets array.
 * This verifies the pattern used in TransactionTable component.
 */
describe("Budget Map Pattern", () => {
  it("builds budgetMap by category_id correctly", () => {
    const budgets: Budget[] = [
      {
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
      },
      {
        id: 2,
        user_id: 1,
        category_id: 2,
        month: 1,
        year: 2026,
        amount: "300.00",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        category: {
          id: 2,
          name: "Groceries",
          icon: "🛒",
          color: "#33FF57",
        },
        spent: "150.00",
        remaining: "150.00",
        percent_used: 50.0,
        is_over_budget: false,
      },
    ];

    // Build map (same pattern as TransactionTable)
    const budgetMap = new Map<number, Budget>();
    budgets.forEach((budget) => {
      budgetMap.set(budget.category_id, budget);
    });

    // Verify map structure
    expect(budgetMap.size).toBe(2);
    expect(budgetMap.get(1)).toEqual(budgets[0]);
    expect(budgetMap.get(2)).toEqual(budgets[1]);
    expect(budgetMap.get(999)).toBeUndefined(); // Non-existent category
  });

  it("handles empty budgets array", () => {
    const budgets: Budget[] = [];
    const budgetMap = new Map<number, Budget>();
    budgets.forEach((budget) => {
      budgetMap.set(budget.category_id, budget);
    });

    expect(budgetMap.size).toBe(0);
  });

  it("allows efficient lookup by category_id", () => {
    const budgets: Budget[] = [
      {
        id: 1,
        user_id: 1,
        category_id: 5,
        month: 1,
        year: 2026,
        amount: "1000.00",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        category: {
          id: 5,
          name: "Transportation",
          icon: "🚗",
          color: "#FF9800",
        },
        spent: "500.00",
        remaining: "500.00",
        percent_used: 50.0,
        is_over_budget: false,
      },
    ];

    const budgetMap = new Map<number, Budget>();
    budgets.forEach((budget) => {
      budgetMap.set(budget.category_id, budget);
    });

    // O(1) lookup
    const budget = budgetMap.get(5);
    expect(budget).toBeDefined();
    expect(budget?.category.name).toBe("Transportation");
  });
});
