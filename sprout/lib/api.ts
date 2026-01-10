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
