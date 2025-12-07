import type { DashboardData } from "@/app/types/dashboard";

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

export async function fetchDashboard(): Promise<DashboardData> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard`);
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

export async function getPlaidLinkToken(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/plaid/link_token/create`);
  if (!response.ok) {
    throw new Error("Failed to get Plaid link token");
  }
  const data = await response.json();
  return data.link_token;
}

export async function exchangePlaidToken(
  public_token: string,
  institution_id?: string | null,
  institution_name?: string | null
): Promise<any> {
  const response = await fetch(
    `${API_BASE_URL}/api/plaid/item/public_token/exchange`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
