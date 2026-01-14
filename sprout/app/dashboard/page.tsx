"use client";
import { useState, useEffect } from "react";
import StatCard from "@/app/components/StatCard";
import SpendingBreakdown from "@/app/components/dashboard/SpendingBreakdown";
import RecentTransactions from "@/app/components/dashboard/RecentTransactions";
import Card from "@/app/components/Card";
import { fetchDashboard } from "@/lib/api";
import type { DashboardData } from "@/app/types/dashboard";
import { createClient } from "@/lib/supabase/client";

const page = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);
        // Get auth token for API call
        const supabase = createClient();
        const {
          data: { session },
        } = await supabase.auth.getSession();
        const token = session?.access_token;
        // Proxy already ensures user is logged in, but we still need token for API
        const data = await fetchDashboard(token);
        setDashboardData(data);
      } catch (error: any) {
        setError(error.message || "Failed to load dashboard data");
        // If unauthorized, Proxy will redirect to login on next navigation
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!dashboardData) {
    return <div>No dashboard data available</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex justify-between items-center mx-4 my-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      </div>
      <div className="grid grid-cols-12 gap-4 p-4 mx-6">
        <div className="col-span-12 md:col-span-3 flex">
          <StatCard title="Income" value={dashboardData?.income || 0} />
        </div>
        <div className="col-span-12 md:col-span-3 flex">
          <StatCard title="Expenses" value={dashboardData?.expenses || 0} />
        </div>
        <div className="col-span-12 md:col-span-3 flex">
          <StatCard title="Savings" value={dashboardData?.savings || 0} />
        </div>
        <div className="col-span-12 md:col-span-3 flex">
          <StatCard title="Assets" value={dashboardData?.assets || 0} />
        </div>
        <div className="col-span-12 md:col-span-5 flex">
          <SpendingBreakdown data={dashboardData?.spendingBreakdown || []} />
        </div>
        <div className="col-span-12 md:col-span-7 flex">
          <RecentTransactions
            transactions={dashboardData?.recentTransactions || []}
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
          <StatCard title="Net Worth" value={dashboardData?.netWorth || 0} />
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
