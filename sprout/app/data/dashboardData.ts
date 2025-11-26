interface DashboardData {
  income: number;
  expenses: number;
  savings: number;
  assets: number;
  netWorth: number;
  spendingBreakdown: {
    category: string;
    amount: number;
    percentage: number;
  }[];
  recentTransactions: {
    id: string;
    description: string;
    amount: number;
    date: string;
    type: "income" | "expense";
  }[];
}

export const mockDashboardData: DashboardData = {
  income: 8500,
  expenses: 4200,
  savings: 4300,
  assets: 125000,
  netWorth: 129300,
  spendingBreakdown: [
    { category: "Housing", amount: 1500, percentage: 36 },
    { category: "Food", amount: 800, percentage: 19 },
    { category: "Transport", amount: 600, percentage: 14 },
    { category: "Entertainment", amount: 500, percentage: 12 },
    { category: "Utilities", amount: 400, percentage: 10 },
    { category: "Other", amount: 400, percentage: 9 },
  ],
  recentTransactions: [
    { id: "1", description: "Salary", amount: 8500, date: "2025-01-01", type: "income" },
    { id: "2", description: "Rent", amount: 1500, date: "2025-01-02", type: "expense" },
    { id: "3", description: "Groceries", amount: 800, date: "2025-01-03", type: "expense" },
    { id: "4", description: "Transport", amount: 600, date: "2025-01-04", type: "expense" },
    { id: "5", description: "Entertainment", amount: 500, date: "2025-01-05", type: "expense" },
  ],
};
