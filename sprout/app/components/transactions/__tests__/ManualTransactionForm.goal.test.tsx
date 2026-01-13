import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ManualTransactionForm } from "../ManualTransactionForm";
import type { Category, Account } from "@/app/types/transactions";
import type { Goal } from "@/app/types/goals";

const mockCategories: Category[] = [
  { id: 1, name: "Dining", icon: "🍽️", color: "#FF5733" },
];

const mockAccounts: Account[] = [
  { id: 1, name: "Checking", account_type: "checking" },
];

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
  {
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
  },
];

const mockOnSubmit = vi.fn();
const mockOnClose = vi.fn();

describe("ManualTransactionForm - Goal Selection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows goal dropdown only for income transactions", async () => {
    render(
      <ManualTransactionForm
        isOpen={true}
        onClose={mockOnClose}
        categories={mockCategories}
        accounts={mockAccounts}
        goals={mockGoals}
        onSubmit={mockOnSubmit}
      />
    );

    // Default is expense, so goal dropdown should not be visible
    expect(screen.queryByLabelText(/goal/i)).not.toBeInTheDocument();

    // Switch to income (using button role, not label)
    const incomeButton = screen.getByRole("button", { name: /income/i });
    await userEvent.click(incomeButton);

    // Now goal dropdown should be visible
    expect(screen.getByLabelText(/goal/i)).toBeInTheDocument();
  });

  it("hides goal dropdown for expense transactions", async () => {
    render(
      <ManualTransactionForm
        isOpen={true}
        onClose={mockOnClose}
        categories={mockCategories}
        accounts={mockAccounts}
        goals={mockGoals}
        onSubmit={mockOnSubmit}
      />
    );

    // Ensure expense is selected (using button role, not label)
    const expenseButton = screen.getByRole("button", { name: /expense/i });
    await userEvent.click(expenseButton);

    // Goal dropdown should not be visible
    expect(screen.queryByLabelText(/goal/i)).not.toBeInTheDocument();
  });

  it("displays all active goals in dropdown", async () => {
    render(
      <ManualTransactionForm
        isOpen={true}
        onClose={mockOnClose}
        categories={mockCategories}
        accounts={mockAccounts}
        goals={mockGoals}
        onSubmit={mockOnSubmit}
      />
    );

    // Switch to income to show goal dropdown (using button role, not label)
    const incomeButton = screen.getByRole("button", { name: /income/i });
    await userEvent.click(incomeButton);

    const goalSelect = screen.getByLabelText(/goal/i);
    await userEvent.click(goalSelect);

    // Should show all goals
    expect(screen.getByText("Emergency Fund")).toBeInTheDocument();
    expect(screen.getByText("Vacation")).toBeInTheDocument();
  });

  it("includes 'No goal' option in dropdown", async () => {
    render(
      <ManualTransactionForm
        isOpen={true}
        onClose={mockOnClose}
        categories={mockCategories}
        accounts={mockAccounts}
        goals={mockGoals}
        onSubmit={mockOnSubmit}
      />
    );

    // Switch to income (using button role, not label)
    const incomeButton = screen.getByRole("button", { name: /income/i });
    await userEvent.click(incomeButton);

    const goalSelect = screen.getByLabelText(/goal/i);
    expect(goalSelect).toHaveValue(""); // Default is empty (no goal)
    expect(screen.getByText("No goal")).toBeInTheDocument();
  });

  it("submits goal_id when goal is selected", async () => {
    const user = userEvent.setup();

    render(
      <ManualTransactionForm
        isOpen={true}
        onClose={mockOnClose}
        categories={mockCategories}
        accounts={mockAccounts}
        goals={mockGoals}
        onSubmit={mockOnSubmit}
      />
    );

    // Fill form
    await user.type(screen.getByLabelText(/description/i), "Salary");
    await user.type(screen.getByLabelText(/amount/i), "1000");
    
    // Switch to income (using button role, not label)
    await user.click(screen.getByRole("button", { name: /income/i }));

    // Select goal
    const goalSelect = screen.getByLabelText(/goal/i);
    await user.selectOptions(goalSelect, "1"); // Emergency Fund

    // Submit
    const submitButton = screen.getByRole("button", { name: /add transaction/i });
    await user.click(submitButton);

    // Verify goal_id is included in submission
    expect(mockOnSubmit).toHaveBeenCalled();
    const submittedData = mockOnSubmit.mock.calls[0][0];
    expect(submittedData.goal_id).toBe(1);
  });

  it("submits null goal_id when no goal is selected", async () => {
    const user = userEvent.setup();

    render(
      <ManualTransactionForm
        isOpen={true}
        onClose={mockOnClose}
        categories={mockCategories}
        accounts={mockAccounts}
        goals={mockGoals}
        onSubmit={mockOnSubmit}
      />
    );

    // Fill form
    await user.type(screen.getByLabelText(/description/i), "Salary");
    await user.type(screen.getByLabelText(/amount/i), "1000");
    
    // Switch to income (but don't select a goal) - using button role, not label
    await user.click(screen.getByRole("button", { name: /income/i }));

    // Submit without selecting goal
    const submitButton = screen.getByRole("button", { name: /add transaction/i });
    await user.click(submitButton);

    // Verify goal_id is null or undefined
    expect(mockOnSubmit).toHaveBeenCalled();
    const submittedData = mockOnSubmit.mock.calls[0][0];
    expect(submittedData.goal_id).toBeNull();
  });
});
