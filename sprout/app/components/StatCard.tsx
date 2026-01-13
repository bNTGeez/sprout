import React from "react";
import Card from "@/app/components/Card";

interface StatCardProps {
  title: string;
  value: number;
  change?: string;
  changeType?: "increase" | "decrease";
}
const StatCard = ({ title, value, change, changeType }: StatCardProps) => {
  const formatCurrency = (amount: number | string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
    }).format(typeof amount === "number" ? amount : Number(amount));
  };

  const changeColor =
    changeType === "increase"
      ? "text-green-500"
      : changeType === "decrease"
      ? "text-red-500"
      : "text-gray-500";

  return (
    <Card>
      <div className="flex flex-col h-full">
        <h3 className="text-sm font-medium text-gray-900">{title}</h3>
        <div className="text-2xl font-bold font-numbers text-gray-900">
          {formatCurrency(value)}
        </div>
        {change && <p className={`font-numbers ${changeColor}`}>{change}</p>}
      </div>
    </Card>
  );
};

export default StatCard;
