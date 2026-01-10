"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Target,
  Wallet,
  Receipt,
  PieChart,
  LogIn,
  LogOut,
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";

const Sidebar = () => {
  const router = useRouter();
  const pathname = usePathname();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);

  // Check auth state for UI purposes (showing login vs logout button)
  useEffect(() => {
    const loadSession = async () => {
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      setIsLoggedIn(!!session);
      setAuthChecked(true);
    };
    loadSession();
  }, [pathname]);

  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    setIsLoggedIn(false);
    router.push("/login");
  };

  const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/goals", label: "Goals", icon: Target },
    { href: "/budgets", label: "Budgets", icon: Wallet },
    { href: "/transactions", label: "Transactions", icon: Receipt },
    { href: "/accounts", label: "Accounts", icon: PieChart },
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
        {/* Auth actions */}
        <div className="px-4 py-6 border-t border-gray-200">
          {authChecked && (
            <>
              {!isLoggedIn ? (
                <Link
                  href="/login"
                  className="flex items-center gap-2 w-full justify-center rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-all"
                >
                  <LogIn className="w-4 h-4" />
                  Login
                </Link>
              ) : (
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 w-full justify-center rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
