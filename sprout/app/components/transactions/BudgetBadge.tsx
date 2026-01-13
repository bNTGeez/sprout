"use client";

import type { Budget } from "@/app/types/budgets";

interface BudgetBadgeProps {
  budget: Budget | undefined;
}

export function BudgetBadge({ budget }: BudgetBadgeProps) {
  if (!budget) {
    return null;
  }

  const remaining = parseFloat(budget.remaining);
  const isOverBudget = budget.is_over_budget;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
        isOverBudget
          ? "bg-red-100 text-red-800"
          : remaining < parseFloat(budget.amount) * 0.2
          ? "bg-yellow-100 text-yellow-800"
          : "bg-green-100 text-green-800"
      }`}
      title={`${budget.category.name} budget: $${remaining.toFixed(2)} left`}
    >
      💰 ${Math.abs(remaining).toFixed(2)} {isOverBudget ? "over" : "left"}
    </span>
  );
}
