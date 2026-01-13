import { describe, it, expect } from "vitest";
import type {
  Budget,
  BudgetCreateRequest,
  BudgetUpdateRequest,
} from "../types/budgets";
import type {
  Goal,
  GoalCreateRequest,
  GoalUpdateRequest,
} from "../types/goals";
import type {
  Transaction,
  TransactionCreateRequest,
  TransactionUpdateRequest,
  GoalInTransaction,
} from "../types/transactions";

describe("Type Definitions", () => {
  describe("Budget types", () => {
    it("Budget type has all required fields", () => {
      const budget: Budget = {
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

      expect(budget.id).toBe(1);
      expect(budget.spent).toBe("200.00"); // Decimal as string
      expect(budget.percent_used).toBe(40.0); // Float
      expect(budget.is_over_budget).toBe(false);
    });

    it("BudgetCreateRequest has required fields", () => {
      const request: BudgetCreateRequest = {
        category_id: 1,
        month: 1,
        year: 2026,
        amount: "500.00",
      };

      expect(request.category_id).toBe(1);
      expect(request.amount).toBe("500.00");
    });

    it("BudgetUpdateRequest has optional fields", () => {
      const request: BudgetUpdateRequest = {
        amount: "600.00",
      };

      expect(request.amount).toBe("600.00");
    });
  });

  describe("Goal types", () => {
    it("Goal type has all required fields", () => {
      const goal: Goal = {
        id: 1,
        user_id: 1,
        name: "Emergency Fund",
        target_amount: "10000.00",
        current_amount: "5000.00",
        target_date: "2026-12-31",
        monthly_contribution: "500.00",
        is_active: true,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        progress_percent: 50.0,
        remaining: "5000.00",
        on_track: true,
      };

      expect(goal.id).toBe(1);
      expect(goal.target_amount).toBe("10000.00"); // Decimal as string
      expect(goal.progress_percent).toBe(50.0); // Float
      expect(goal.on_track).toBe(true);
    });

    it("Goal can have null optional fields", () => {
      const goal: Goal = {
        id: 2,
        user_id: 1,
        name: "Vacation",
        target_amount: "3000.00",
        current_amount: "1000.00",
        target_date: null,
        monthly_contribution: null,
        is_active: true,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        progress_percent: 33.33,
        remaining: "2000.00",
        on_track: null,
      };

      expect(goal.target_date).toBeNull();
      expect(goal.monthly_contribution).toBeNull();
      expect(goal.on_track).toBeNull();
    });

    it("GoalCreateRequest has required and optional fields", () => {
      const request: GoalCreateRequest = {
        name: "Emergency Fund",
        target_amount: "10000.00",
        target_date: "2026-12-31",
        monthly_contribution: "500.00",
      };

      expect(request.name).toBe("Emergency Fund");
      expect(request.target_date).toBe("2026-12-31");
    });
  });

  describe("Transaction types with goal support", () => {
    it("Transaction includes goal_id and goal", () => {
      const transaction: Transaction = {
        id: 1,
        user_id: 1,
        account_id: 1,
        category_id: 1,
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
        category: {
          id: 1,
          name: "Savings",
          icon: "💰",
          color: "#00FF00",
        },
        account: {
          id: 1,
          name: "Checking",
          account_type: "checking",
        },
        goal: {
          id: 1,
          name: "Emergency Fund",
        },
      };

      expect(transaction.goal_id).toBe(1);
      expect(transaction.goal).not.toBeNull();
      expect(transaction.goal?.name).toBe("Emergency Fund");
    });

    it("Transaction can have null goal_id and goal", () => {
      const transaction: Transaction = {
        id: 2,
        user_id: 1,
        account_id: 1,
        category_id: 1,
        goal_id: null,
        amount: "-100.00",
        date: "2026-01-15",
        description: "Expense",
        normalized_merchant: null,
        is_subscription: false,
        tags: null,
        notes: null,
        created_at: "2026-01-15T00:00:00Z",
        updated_at: "2026-01-15T00:00:00Z",
        category: {
          id: 1,
          name: "Dining",
          icon: "🍽️",
          color: "#FF5733",
        },
        account: {
          id: 1,
          name: "Checking",
          account_type: "checking",
        },
        goal: null,
      };

      expect(transaction.goal_id).toBeNull();
      expect(transaction.goal).toBeNull();
    });

    it("TransactionCreateRequest includes goal_id", () => {
      const request: TransactionCreateRequest = {
        account_id: 1,
        amount: "500.00",
        date: "2026-01-15",
        description: "Savings",
        category_id: null,
        goal_id: 1,
        notes: null,
      };

      expect(request.goal_id).toBe(1);
    });

    it("TransactionUpdateRequest includes goal_id", () => {
      const request: TransactionUpdateRequest = {
        amount: "600.00",
        goal_id: 2,
      };

      expect(request.goal_id).toBe(2);
    });

    it("GoalInTransaction is minimal (id + name only)", () => {
      const goalInTx: GoalInTransaction = {
        id: 1,
        name: "Emergency Fund",
      };

      expect(Object.keys(goalInTx)).toEqual(["id", "name"]);
      expect(goalInTx.id).toBe(1);
      expect(goalInTx.name).toBe("Emergency Fund");
    });
  });
});
