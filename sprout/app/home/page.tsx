import React from "react";
import Hero from "@/app/components/home/Hero";
import Features from "@/app/components/home/Features";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-6">
        <Hero />
        <Features />
      </div>
    </div>
  );
}
