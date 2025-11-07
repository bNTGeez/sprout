import React from "react";
import { LayoutDashboard, Target, Wallet, PieChart } from "lucide-react";

export default function Features() {
  const features = [
    {
      icon: LayoutDashboard,
      title: "Dashboard",
      description: "View your financial overview at a glance",
    },
    {
      icon: Target,
      title: "Goals",
      description: "Set and track your financial goals",
    },
    {
      icon: Wallet,
      title: "Budgets",
      description: "Manage your budgets effectively",
    },
    {
      icon: PieChart,
      title: "Assets",
      description: "Track your assets and investments",
    },
  ];

  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 py-12">
      {features.map((feature) => {
        const Icon = feature.icon;
        return (
          <div
            key={feature.title}
            className="bg-white p-6 rounded-lg shadow-sm border border-gray-200"
          >
            <div className="mb-4">
              <Icon className="w-8 h-8 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {feature.title}
            </h3>
            <p className="text-gray-600 text-sm">{feature.description}</p>
          </div>
        );
      })}
    </div>
  );
}
