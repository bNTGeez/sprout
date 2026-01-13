"use client";

import type { GoalInTransaction } from "@/app/types/transactions";

interface GoalBadgeProps {
  goal: GoalInTransaction | null;
}

export function GoalBadge({ goal }: GoalBadgeProps) {
  if (!goal) {
    return null;
  }

  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
      title={`Linked to goal: ${goal.name}`}
    >
      🎯 {goal.name}
    </span>
  );
}
