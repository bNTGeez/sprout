import { CreditCard, Landmark, DollarSign, TrendingUp, Building2 } from "lucide-react";

export function getAccountIcon(type: string) {
  switch (type) {
    case "depository":
      return Landmark;
    case "credit":
      return CreditCard;
    case "investment":
      return TrendingUp;
    case "cash":
      return DollarSign;
    default:
      return Building2;
  }
}

export function getAccountTypeLabel(type: string): string {
  switch (type) {
    case "depository":
      return "Checking/Savings";
    case "credit":
      return "Credit Card";
    case "investment":
      return "Investment";
    case "cash":
      return "Cash";
    default:
      return type;
  }
}

export function formatCurrency(amount: string | number): string {
  const numAmount = typeof amount === "string" ? parseFloat(amount) : amount;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(numAmount);
}
