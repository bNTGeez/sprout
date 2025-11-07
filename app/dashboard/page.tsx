import React from "react";
import StatCard from "@/app/components/StatCard";
import SpendingBreakdown from "@/app/components/dashboard/SpendingBreakdown";
import RecentTransactions from "@/app/components/dashboard/RecentTransactions";
import { mockDashboardData } from "@/app/data/dashboardData";
import Card from "@/app/components/Card";

const page = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div>
        <h1 className="mx-4 my-6 text-2xl font-bold text-gray-900">
          Dashboard
        </h1>
      </div>
      <div className="grid grid-cols-12 gap-4 p-4 mx-6">
        <div className="col-span-12 md:col-span-3 flex">
          <StatCard title="Income" value={mockDashboardData.income} />
        </div>
        <div className="col-span-12 md:col-span-3 flex">
          <StatCard title="Expenses" value={mockDashboardData.expenses} />
        </div>
        <div className="col-span-12 md:col-span-3 flex">
          <StatCard title="Savings" value={mockDashboardData.savings} />
        </div>
        <div className="col-span-12 md:col-span-3 flex">
          <StatCard title="Assets" value={mockDashboardData.assets} />
        </div>
        <div className="col-span-12 md:col-span-5 flex">
          <SpendingBreakdown data={mockDashboardData.spendingBreakdown} />
        </div>
        <div className="col-span-12 md:col-span-7 flex">
          <RecentTransactions
            transactions={mockDashboardData.recentTransactions}
          />
        </div>
        <div className="col-span-12 md:col-span-6 flex">
          <Card>
            <h2 className="text-lg font-bold text-gray-900 mb-4">Budget</h2>
            <p className="text-sm text-gray-600">
              Budget tracking will go here
            </p>
          </Card>
        </div>
        <div className="col-span-12 md:col-span-6 flex">
          <Card>
            <h2 className="text-lg font-bold text-gray-900 mb-4">
              Savings and Investments
            </h2>
            <p className="text-sm text-gray-600">
              Savings tracking will go here
            </p>
          </Card>
        </div>
        <div className="col-span-12 md:col-span-5 flex">
          <StatCard title="Net Worth" value={mockDashboardData.netWorth} />
        </div>
        <div className="col-span-12 md:col-span-7 flex">
          <Card>
            <h2 className="text-lg font-bold text-gray-900 mb-4">Insights</h2>
            <p className="text-sm text-gray-600">
              Financial insights will go here
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default page;
