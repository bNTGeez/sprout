export interface DashboardData {
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