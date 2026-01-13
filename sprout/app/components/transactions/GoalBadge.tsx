"use client";

import { Target } from "lucide-react";
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
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
      title={`Linked to goal: ${goal.name}`}
    >
      <Target className="w-3 h-3" />
      {goal.name}
    </span>
  );
}
