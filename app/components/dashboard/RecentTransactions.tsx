"use client";

import React, { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import Card from "@/app/components/Card";

interface RecentTransactionsProps {
  transactions: {
    id: string;
    description: string;
    amount: number;
    date: string;
    type: "income" | "expense";
  }[];
}

const RecentTransactions = ({ transactions }: RecentTransactionsProps) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  // Transform transaction data for line chart
  const chartData = useMemo(() => {
    // Group transactions by date
    const grouped = transactions.reduce((acc, transaction) => {
      const date = transaction.date;
      if (!acc[date]) {
        acc[date] = { date, income: 0, expenses: 0 };
      }
      if (transaction.type === "income") {
        acc[date].income += Math.abs(transaction.amount);
      } else {
        acc[date].expenses += Math.abs(transaction.amount);
      }
      return acc;
    }, {} as Record<string, { date: string; income: number; expenses: number }>);

    // Convert to array and sort by date
    return Object.values(grouped)
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map((item) => ({
        date: formatDate(item.date),
        fullDate: item.date,
        income: item.income,
        expenses: item.expenses,
      }));
  }, [transactions]);

  const transactionTypeColor = (type: "income" | "expense") => {
    return type === "income" ? "text-green-600" : "text-red-600";
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 mb-2">
            {payload[0]?.payload?.fullDate
              ? formatDate(payload[0].payload.fullDate)
              : ""}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card>
      <h2 className="text-lg font-bold text-gray-900 mb-4">
        Recent Transactions
      </h2>

      {/* Line Chart */}
      {chartData.length > 0 && (
        <div className="w-full h-[250px] mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                stroke="#6b7280"
                style={{ fontSize: "12px" }}
              />
              <YAxis
                stroke="#6b7280"
                style={{ fontSize: "12px" }}
                tickFormatter={(value) => `$${value.toLocaleString()}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
              <Line
                type="monotone"
                dataKey="income"
                name="Income"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: "#10b981", r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="expenses"
                name="Expenses"
                stroke="#ef4444"
                strokeWidth={2}
                dot={{ fill: "#ef4444", r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Transaction List */}
      <div className="space-y-3">
        {transactions.map((transaction) => (
          <div
            key={transaction.id}
            className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0"
          >
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-900">
                {transaction.description}
              </div>
              <div className="text-xs text-gray-500">
                {formatDate(transaction.date)}
              </div>
            </div>
            <div
              className={`text-sm font-semibold ${transactionTypeColor(
                transaction.type
              )}`}
            >
              {transaction.type === "income" ? "+" : "-"}
              {formatCurrency(Math.abs(transaction.amount))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default RecentTransactions;
