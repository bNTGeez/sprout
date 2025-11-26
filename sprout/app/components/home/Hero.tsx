import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function Hero() {
  return (
    <div className="text-center py-20">
      <h1 className="text-5xl font-bold text-gray-900 mb-4">
        Welcome to <span className="text-blue-600">Sprout</span>
      </h1>
      <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
        Your personal finance companion. Track budgets, set goals, and manage
        your money with ease.
      </p>
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
      >
        Get Started
        <ArrowRight className="w-5 h-5" />
      </Link>
    </div>
  );
}
