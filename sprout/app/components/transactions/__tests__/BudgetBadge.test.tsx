import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { BudgetBadge } from "../BudgetBadge";
import type { Budget } from "@/app/types/budgets";

describe("BudgetBadge", () => {
  it("renders nothing when budget is undefined", () => {
    const { container } = render(<BudgetBadge budget={undefined} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders budget badge with remaining amount", () => {
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

    render(<BudgetBadge budget={budget} />);
    
    expect(screen.getByText(/300.00/)).toBeInTheDocument();
    expect(screen.getByText(/left/)).toBeInTheDocument();
  });

  it("shows 'over' when budget is exceeded", () => {
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
      spent: "600.00",
      remaining: "-100.00",
      percent_used: 120.0,
      is_over_budget: true,
    };

    render(<BudgetBadge budget={budget} />);
    
    expect(screen.getByText(/100.00/)).toBeInTheDocument();
    expect(screen.getByText(/over/)).toBeInTheDocument();
  });

  it("applies correct styling for over budget", () => {
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
      spent: "600.00",
      remaining: "-100.00",
      percent_used: 120.0,
      is_over_budget: true,
    };

    const { container } = render(<BudgetBadge budget={budget} />);
    const badge = container.querySelector("span");
    
    expect(badge).toHaveClass("bg-red-100", "text-red-800");
  });
});
