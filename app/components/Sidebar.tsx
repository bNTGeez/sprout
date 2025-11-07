"use client";
import Link from "next/link";
import {
  LayoutDashboard,
  Target,
  Wallet,
  Receipt,
  PieChart,
} from "lucide-react";

const Sidebar = () => {
  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/goals", label: "Goals", icon: Target },
    { href: "/budgets", label: "Budgets", icon: Wallet },
    { href: "/transactions", label: "Transactions", icon: Receipt },
    { href: "/assets", label: "Assets", icon: PieChart },
  ];

  return (
    <aside className="w-64 min-h-screen bg-white border-r border-gray-200 shadow-sm">
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="px-6 py-6 border-b border-gray-200">
          <Link href="/">
            <h1 className="text-2xl font-bold text-gray-900">Sprout</h1>
          </Link>
          <p className="text-sm text-gray-500 mt-1">Finance made simple</p>
        </div>
        {/* Nav */}
        <nav className="flex-1 px-4 py-6">
          <div className="flex flex-col gap-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-lg font-medium text-gray-700 hover:bg-gray-50 hover:text-gray-900 transition-all duration-200"
                >
                  <Icon className="text-gray-500 w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;
