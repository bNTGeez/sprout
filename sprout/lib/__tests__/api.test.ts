import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  fetchBudgets,
  createBudget,
  updateBudget,
  deleteBudget,
  fetchGoals,
  createGoal,
  updateGoal,
  deleteGoal,
} from "../api";
import type { Budget, BudgetCreateRequest, BudgetUpdateRequest } from "@/app/types/budgets";
import type { Goal, GoalCreateRequest, GoalUpdateRequest } from "@/app/types/goals";

// Mock fetch globally
global.fetch = vi.fn();

const mockToken = "test-token";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

describe("Budgets API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("fetchBudgets", () => {
    it("fetches budgets without filters", async () => {
      const mockBudgets: Budget[] = [
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
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockBudgets,
      });

      const result = await fetchBudgets(mockToken);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/budgets`,
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
          },
        }
      );
      expect(result).toEqual(mockBudgets);
    });

    it("fetches budgets with month and year filters", async () => {
      const mockBudgets: Budget[] = [];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockBudgets,
      });

      await fetchBudgets(mockToken, 1, 2026);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/budgets?month=1&year=2026`,
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
          },
        }
      );
    });

    it("throws error on 401", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      await expect(fetchBudgets(mockToken)).rejects.toThrow("Unauthorized");
    });
  });

  describe("createBudget", () => {
    it("creates a budget successfully", async () => {
      const request: BudgetCreateRequest = {
        category_id: 1,
        month: 1,
        year: 2026,
        amount: "500.00",
      };

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
        spent: "0.00",
        remaining: "500.00",
        percent_used: 0.0,
        is_over_budget: false,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockBudget,
      });

      const result = await createBudget(mockToken, request);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/budgets`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${mockToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(request),
        }
      );
      expect(result).toEqual(mockBudget);
    });
  });

  describe("updateBudget", () => {
    it("updates a budget successfully", async () => {
      const request: BudgetUpdateRequest = {
        amount: "600.00",
      };

      const mockBudget: Budget = {
        id: 1,
        user_id: 1,
        category_id: 1,
        month: 1,
        year: 2026,
        amount: "600.00",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        category: {
          id: 1,
          name: "Dining",
          icon: "🍽️",
          color: "#FF5733",
        },
        spent: "200.00",
        remaining: "400.00",
        percent_used: 33.33,
        is_over_budget: false,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockBudget,
      });

      const result = await updateBudget(mockToken, 1, request);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/budgets/1`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${mockToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(request),
        }
      );
      expect(result).toEqual(mockBudget);
    });

    it("throws error on 404", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(updateBudget(mockToken, 999, { amount: "100.00" })).rejects.toThrow(
        "Budget not found"
      );
    });
  });

  describe("deleteBudget", () => {
    it("deletes a budget successfully", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      await deleteBudget(mockToken, 1);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/budgets/1`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${mockToken}`,
          },
        }
      );
    });
  });
});

describe("Goals API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("fetchGoals", () => {
    it("fetches goals without filter", async () => {
      const mockGoals: Goal[] = [
        {
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
        },
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockGoals,
      });

      const result = await fetchGoals(mockToken);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/goals`,
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
          },
        }
      );
      expect(result).toEqual(mockGoals);
    });

    it("fetches goals with is_active filter", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [],
      });

      await fetchGoals(mockToken, true);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/goals?is_active=true`,
        {
          headers: {
            Authorization: `Bearer ${mockToken}`,
          },
        }
      );
    });
  });

  describe("createGoal", () => {
    it("creates a goal successfully", async () => {
      const request: GoalCreateRequest = {
        name: "Emergency Fund",
        target_amount: "10000.00",
        target_date: "2026-12-31",
        monthly_contribution: "500.00",
      };

      const mockGoal: Goal = {
        id: 1,
        user_id: 1,
        name: "Emergency Fund",
        target_amount: "10000.00",
        current_amount: "0.00",
        target_date: "2026-12-31",
        monthly_contribution: "500.00",
        is_active: true,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        progress_percent: 0.0,
        remaining: "10000.00",
        on_track: null,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockGoal,
      });

      const result = await createGoal(mockToken, request);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/goals`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${mockToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(request),
        }
      );
      expect(result).toEqual(mockGoal);
    });
  });

  describe("updateGoal", () => {
    it("updates a goal successfully", async () => {
      const request: GoalUpdateRequest = {
        name: "Updated Goal",
        target_amount: "15000.00",
      };

      const mockGoal: Goal = {
        id: 1,
        user_id: 1,
        name: "Updated Goal",
        target_amount: "15000.00",
        current_amount: "5000.00",
        target_date: null,
        monthly_contribution: null,
        is_active: true,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
        progress_percent: 33.33,
        remaining: "10000.00",
        on_track: null,
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockGoal,
      });

      const result = await updateGoal(mockToken, 1, request);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/goals/1`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${mockToken}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(request),
        }
      );
      expect(result).toEqual(mockGoal);
    });
  });

  describe("deleteGoal", () => {
    it("deletes a goal successfully", async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        status: 204,
      });

      await deleteGoal(mockToken, 1);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/goals/1`,
        {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${mockToken}`,
          },
        }
      );
    });
  });
});
