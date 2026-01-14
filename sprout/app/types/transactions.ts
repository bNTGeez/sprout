// Transaction types
export interface Category {
  id: number;
  name: string;
  icon: string | null;
  color: string | null;
}

export interface Account {
  id: number;
  name: string;
  account_type: string;
}

export interface GoalInTransaction {
  id: number;
  name: string;
}

export interface Transaction {
  id: number;
  user_id: number;
  account_id: number;
  category_id: number | null;
  goal_id: number | null;
  amount: string; // Decimal as string
  date: string; // ISO date
  description: string;
  normalized_merchant: string | null;
  is_subscription: boolean;
  tags: string[] | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  category: Category | null;
  account: Account;
  goal: GoalInTransaction | null;
}

export interface TransactionListResponse {
  transactions: Transaction[];
  total: number;
  page: number;
  pages: number;
}

export interface TransactionStatsResponse {
  total: number;
  income: string; // Decimal as string
  expenses: string; // Decimal as string
}

export interface TransactionFilters {
  page?: number;
  limit?: number;
  search?: string;
  category_id?: number;
  date_from?: string;
  date_to?: string;
  min_amount?: string;
  max_amount?: string;
  is_uncategorized?: boolean;
}

export interface TransactionCreateRequest {
  account_id: number;
  amount: string;
  date: string;
  description: string;
  category_id?: number | null;
  goal_id?: number | null;
  notes?: string | null;
  normalized_merchant?: string | null;
}

export interface TransactionUpdateRequest {
  description?: string;
  amount?: string;
  date?: string;
  category_id?: number | null;
  goal_id?: number | null;
  notes?: string | null;
  normalized_merchant?: string | null;
}
