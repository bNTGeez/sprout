// Budget types

export interface Budget {
  id: number;
  user_id: number;
  category_id: number;
  month: number;
  year: number;
  amount: string; // Decimal as string
  created_at: string;
  updated_at: string;
  category: {
    id: number;
    name: string;
    icon: string | null;
    color: string | null;
  };
  // Computed fields
  spent: string; // Decimal as string
  remaining: string; // Decimal as string
  percent_used: number; // Float
  is_over_budget: boolean;
}

export interface BudgetCreateRequest {
  category_id: number;
  month: number;
  year: number;
  amount: string; // Decimal as string
}

export interface BudgetUpdateRequest {
  amount?: string; // Decimal as string
}
