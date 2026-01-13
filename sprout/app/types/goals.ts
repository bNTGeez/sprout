// Goal types

export interface Goal {
  id: number;
  user_id: number;
  name: string;
  target_amount: string; // Decimal as string
  current_amount: string; // Decimal as string
  target_date: string | null; // ISO date or null
  monthly_contribution: string | null; // Decimal as string or null
  is_active: boolean;
  created_at: string;
  updated_at: string;
  // Computed fields
  progress_percent: number; // Float
  remaining: string; // Decimal as string
  on_track: boolean | null; // Null if no target_date or monthly_contribution, or if goal is met
  is_met: boolean; // True if current_amount >= target_amount
}

export interface GoalCreateRequest {
  name: string;
  target_amount: string; // Decimal as string
  target_date?: string | null; // ISO date
  monthly_contribution?: string | null; // Decimal as string
}

export interface GoalUpdateRequest {
  name?: string;
  target_amount?: string; // Decimal as string
  target_date?: string | null; // ISO date
  monthly_contribution?: string | null; // Decimal as string
  is_active?: boolean;
}

// Minimal goal for transaction badges
export interface GoalInTransaction {
  id: number;
  name: string;
}
