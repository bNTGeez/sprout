import type { DashboardData } from "@/app/types/dashboard";
import type {
  Transaction,
  TransactionListResponse,
  TransactionFilters,
  Category,
  Account as TransactionAccount,
  TransactionCreateRequest,
  TransactionUpdateRequest,
} from "@/app/types/transactions";
import type { Account } from "@/app/types/accounts";
import type {
  Budget,
  BudgetCreateRequest,
  BudgetUpdateRequest,
} from "@/app/types/budgets";
import type {
  Goal,
  GoalCreateRequest,
  GoalUpdateRequest,
} from "@/app/types/goals";

// Re-export types for convenience
export type {
  Transaction,
  TransactionListResponse,
  TransactionFilters,
  Category,
  Account,
  TransactionCreateRequest,
  TransactionUpdateRequest,
};

interface BackendDashboardData {
  income: number;
  expenses: number;
  savings: number;
  assets: number;
  net_worth: number;
  spending_breakdown: {
    category: string;
    amount: number;
    percentage: number;
  }[];
  recent_transactions: {
    id: number;
    description: string;
    amount: number;
    date: string;
    type: "income" | "expense";
  }[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDashboard(token?: string): Promise<DashboardData> {
  if (!token) {
    console.warn("fetchDashboard called without token");
  } else {
    console.info(
      "fetchDashboard sending token (preview):",
      token.substring(0, 16)
    );
  }

  const response = await fetch(`${API_BASE_URL}/api/dashboard`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }
  if (!response.ok) {
    throw new Error("Failed to fetch dashboard data");
  }
  const data: BackendDashboardData = await response.json();

  return {
    income: data.income,
    expenses: data.expenses,
    savings: data.savings,
    assets: data.assets,
    netWorth: data.net_worth,
    spendingBreakdown: data.spending_breakdown,
    recentTransactions: data.recent_transactions.map((tx) => ({
      id: String(tx.id),
      description: tx.description,
      amount: tx.amount,
      date: tx.date,
      type: tx.type,
    })),
  };
}

export async function getPlaidLinkToken(token: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/plaid/link_token/create`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(
      errorData.detail || `Failed to get Plaid link token: ${response.status}`
    );
  }
  const data = await response.json();
  return data.link_token;
}

export async function exchangePlaidToken(
  public_token: string,
  token: string,
  institution_id?: string | null,
  institution_name?: string | null
): Promise<any> {
  const response = await fetch(
    `${API_BASE_URL}/api/plaid/item/public_token/exchange`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        public_token,
        institution_id: institution_id || null,
        institution_name: institution_name || null,
      }),
    }
  );

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(
      errorData.detail || `Failed to exchange Plaid token: ${response.status}`
    );
  }

  return response.json();
}

export async function getPlaidItems(token: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/plaid/items`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to load Plaid items");
  }

  return response.json();
}

export async function fetchTransactions(
  token: string,
  filters?: TransactionFilters
): Promise<TransactionListResponse> {
  const params = new URLSearchParams();

  if (filters?.page) params.append("page", filters.page.toString());
  if (filters?.limit) params.append("limit", filters.limit.toString());
  if (filters?.search) params.append("search", filters.search);
  if (filters?.category_id)
    params.append("category_id", filters.category_id.toString());
  if (filters?.date_from) params.append("date_from", filters.date_from);
  if (filters?.date_to) params.append("date_to", filters.date_to);
  if (filters?.min_amount) params.append("min_amount", filters.min_amount);
  if (filters?.max_amount) params.append("max_amount", filters.max_amount);
  if (filters?.is_uncategorized !== undefined) {
    params.append("is_uncategorized", filters.is_uncategorized.toString());
  }

  const url = `${API_BASE_URL}/api/transactions${
    params.toString() ? `?${params.toString()}` : ""
  }`;

  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }

  if (!response.ok) {
    throw new Error("Failed to fetch transactions");
  }

  return response.json();
}

export async function fetchCategories(token: string): Promise<Category[]> {
  const response = await fetch(`${API_BASE_URL}/api/categories`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!response.ok) {
    throw new Error("Failed to fetch categories");
  }

  return response.json();
}

export async function fetchAccounts(token: string): Promise<Account[]> {
  const response = await fetch(`${API_BASE_URL}/api/accounts`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }

  if (!response.ok) {
    throw new Error("Failed to fetch accounts");
  }

  return response.json();
}

export interface PlaidItem {
  id: number;
  institution_name: string;
  status: string;
  created_at: string;
}

export interface PlaidItemsResponse {
  plaid_items: PlaidItem[];
}

export async function fetchPlaidItems(token: string): Promise<PlaidItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/plaid/items`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }

  if (!response.ok) {
    throw new Error("Failed to fetch Plaid items");
  }

  const data: PlaidItemsResponse = await response.json();
  return data.plaid_items;
}

export interface PlaidItemStatus {
  plaid_item_id: number;
  institution_name: string;
  status: string;
  accounts_count: number;
  transactions_count: number;
  has_cursor: boolean;
  last_synced: string | null;
}

export async function fetchPlaidItemStatus(
  token: string,
  plaidItemId: number
): Promise<PlaidItemStatus> {
  const response = await fetch(
    `${API_BASE_URL}/api/plaid/status/${plaidItemId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }

  if (response.status === 404) {
    throw new Error("Plaid item not found");
  }

  if (!response.ok) {
    throw new Error("Failed to fetch Plaid item status");
  }

  return response.json();
}

export async function getReauthLinkToken(
  token: string,
  plaidItemId: number
): Promise<string> {
  // For reauth, we pass the plaid_item_id to get a link token for that specific item
  const response = await fetch(
    `${API_BASE_URL}/api/plaid/link_token/create?plaid_item_id=${plaidItemId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(errorData.detail || "Failed to get reauth link token");
  }

  const data = await response.json();
  return data.link_token;
}

export async function triggerPlaidSync(
  token: string,
  plaidItemId: number
): Promise<{ success: boolean; accounts_synced: number; transactions: { added: number; modified: number; removed: number } }> {
  const response = await fetch(
    `${API_BASE_URL}/api/plaid/sync?plaid_item_id=${plaidItemId}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }

  if (response.status === 404) {
    throw new Error("Plaid item not found");
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to trigger sync" }));
    throw new Error(errorData.detail || "Failed to trigger sync");
  }

  return response.json();
}

export async function createTransaction(
  token: string,
  data: TransactionCreateRequest
): Promise<Transaction> {
  // Add timeout to prevent hanging
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

  try {
    const response = await fetch(`${API_BASE_URL}/api/transactions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.status === 401) {
      throw new Error("Unauthorized: Please log in again");
    }

    if (response.status === 400) {
      const error = await response.json();
      throw new Error(error.detail || "Invalid transaction data");
    }

    if (!response.ok) {
      throw new Error("Failed to create transaction");
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(
        "Request timed out. Please check your connection and try again."
      );
    }
    throw error;
  }
}

export async function updateTransaction(
  token: string,
  id: number,
  data: TransactionUpdateRequest
): Promise<Transaction> {
  console.log("Updating transaction:", id, data);

  // Add timeout to prevent hanging
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

  try {
    const response = await fetch(`${API_BASE_URL}/api/transactions/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.status === 401) {
      throw new Error("Unauthorized: Please log in again");
    }

    if (response.status === 404) {
      throw new Error("Transaction not found");
    }

    if (response.status === 400 || response.status === 422) {
      const error = await response.json();
      console.error("Update error:", error);
      throw new Error(
        error.detail || JSON.stringify(error) || "Invalid transaction data"
      );
    }

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Update failed:", errorText);
      throw new Error("Failed to update transaction");
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(
        "Request timed out. Please check your connection and try again."
      );
    }
    throw error;
  }
}

export async function deleteTransaction(
  token: string,
  id: number
): Promise<void> {
  // Add timeout to prevent hanging
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

  try {
    const response = await fetch(`${API_BASE_URL}/api/transactions/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.status === 401) {
      throw new Error("Unauthorized: Please log in again");
    }

    if (response.status === 404) {
      throw new Error("Transaction not found");
    }

    if (!response.ok) {
      throw new Error("Failed to delete transaction");
    }
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(
        "Request timed out. Please check your connection and try again."
      );
    }
    throw error;
  }
}

export async function fetchUncategorizedCount(token: string): Promise<number> {
  const response = await fetch(
    `${API_BASE_URL}/api/transactions/uncategorized/count`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }

  if (!response.ok) {
    throw new Error("Failed to fetch uncategorized count");
  }

  const data = await response.json();
  return data.count;
}

export async function processBatchUncategorized(
  token: string,
  limit: number = 100
): Promise<{ message: string }> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout for batch

  try {
    const response = await fetch(
      `${API_BASE_URL}/api/agents/process-uncategorized?limit=${limit}`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        signal: controller.signal,
      }
    );

    clearTimeout(timeoutId);

    if (response.status === 401) {
      throw new Error("Unauthorized: Please log in again");
    }

    if (!response.ok) {
      throw new Error("Failed to start batch processing");
    }

    return response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(
        "Request timed out. Please check your connection and try again."
      );
    }
    throw error;
  }
}

// ============================================================================
// Budgets API
// ============================================================================

export async function fetchBudgets(
  token: string,
  month?: number,
  year?: number
): Promise<Budget[]> {
  const params = new URLSearchParams();
  if (month !== undefined) params.append("month", String(month));
  if (year !== undefined) params.append("year", String(year));
  
  const url = `${API_BASE_URL}/api/budgets${params.toString() ? `?${params.toString()}` : ""}`;
  
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }
  
  if (!response.ok) {
    throw new Error("Failed to fetch budgets");
  }
  
  return response.json();
}

export async function createBudget(
  token: string,
  data: BudgetCreateRequest
): Promise<Budget> {
  const response = await fetch(`${API_BASE_URL}/api/budgets`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  
  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to create budget" }));
    throw new Error(errorData.detail || "Failed to create budget");
  }
  
  return response.json();
}

export async function updateBudget(
  token: string,
  budgetId: number,
  data: BudgetUpdateRequest
): Promise<Budget> {
  const response = await fetch(`${API_BASE_URL}/api/budgets/${budgetId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  
  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }
  
  if (response.status === 404) {
    throw new Error("Budget not found");
  }
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to update budget" }));
    throw new Error(errorData.detail || "Failed to update budget");
  }
  
  return response.json();
}

export async function deleteBudget(
  token: string,
  budgetId: number
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/budgets/${budgetId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }
  
  if (response.status === 404) {
    throw new Error("Budget not found");
  }
  
  if (!response.ok) {
    throw new Error("Failed to delete budget");
  }
}

// ============================================================================
// Goals API
// ============================================================================

export async function fetchGoals(
  token: string,
  isActive?: boolean
): Promise<Goal[]> {
  const params = new URLSearchParams();
  if (isActive !== undefined) params.append("is_active", String(isActive));
  
  const url = `${API_BASE_URL}/api/goals${params.toString() ? `?${params.toString()}` : ""}`;
  
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }
  
  if (!response.ok) {
    throw new Error("Failed to fetch goals");
  }
  
  return response.json();
}

export async function createGoal(
  token: string,
  data: GoalCreateRequest
): Promise<Goal> {
  const response = await fetch(`${API_BASE_URL}/api/goals`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  
  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to create goal" }));
    throw new Error(errorData.detail || "Failed to create goal");
  }
  
  return response.json();
}

export async function updateGoal(
  token: string,
  goalId: number,
  data: GoalUpdateRequest
): Promise<Goal> {
  const response = await fetch(`${API_BASE_URL}/api/goals/${goalId}`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  
  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }
  
  if (response.status === 404) {
    throw new Error("Goal not found");
  }
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: "Failed to update goal" }));
    throw new Error(errorData.detail || "Failed to update goal");
  }
  
  return response.json();
}

export async function deleteGoal(
  token: string,
  goalId: number
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/goals/${goalId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  
  if (response.status === 401) {
    throw new Error("Unauthorized: Please log in again");
  }
  
  if (response.status === 404) {
    throw new Error("Goal not found");
  }
  
  if (!response.ok) {
    throw new Error("Failed to delete goal");
  }
}
