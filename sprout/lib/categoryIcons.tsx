import {
  UtensilsCrossed,
  ShoppingBag,
  Car,
  Home,
  Film,
  Music,
  Gamepad2,
  Dumbbell,
  Heart,
  GraduationCap,
  Briefcase,
  Plane,
  Fuel,
  Stethoscope,
  Pill,
  Scissors,
  Shirt,
  Baby,
  Gift,
  CreditCard,
  Wallet,
  Banknote,
  TrendingUp,
  Building2,
  Tag,
  HelpCircle,
  Shield,
  FileText,
} from "lucide-react";
import type { ComponentType } from "react";

// Map category names to lucide-react icons
const categoryIconMap: Record<string, ComponentType<{ className?: string }>> = {
  // Food & Dining
  dining: UtensilsCrossed,
  "dining out": UtensilsCrossed,
  restaurant: UtensilsCrossed,
  food: UtensilsCrossed,
  groceries: ShoppingBag,
  grocery: ShoppingBag,

  // Transportation
  transportation: Car,
  transport: Car,
  car: Car,
  gas: Fuel,
  fuel: Fuel,
  parking: Car,
  taxi: Car,
  uber: Car,
  lyft: Car,

  // Shopping
  shopping: ShoppingBag,
  retail: ShoppingBag,
  clothing: Shirt,
  apparel: Shirt,

  // Entertainment
  entertainment: Film,
  movies: Film,
  music: Music,
  games: Gamepad2,
  gaming: Gamepad2,

  // Health & Fitness
  health: Heart,
  fitness: Dumbbell,
  gym: Dumbbell,
  medical: Stethoscope,
  pharmacy: Pill,

  // Services
  services: Scissors,
  haircut: Scissors,
  personal: Scissors,

  // Home & Utilities
  home: Home,
  housing: Home,
  utilities: Home,
  rent: Home,
  mortgage: Home,

  // Education
  education: GraduationCap,
  school: GraduationCap,
  tuition: GraduationCap,

  // Work & Business
  business: Briefcase,
  work: Briefcase,
  office: Briefcase,

  // Travel
  travel: Plane,
  flights: Plane,
  hotels: Building2,
  accommodation: Building2,

  // Financial
  income: TrendingUp,
  salary: Banknote,
  investment: TrendingUp,
  savings: Wallet,
  transfer: CreditCard,

  // Other
  gifts: Gift,
  baby: Baby,
  pets: Heart,
  subscriptions: CreditCard,
  bills: Banknote,
  insurance: Shield,
  taxes: FileText,
};

// Default icon for uncategorized or unknown categories
const DefaultIcon = Tag;

/**
 * Get the appropriate icon component for a category name
 */
export function getCategoryIcon(
  categoryName: string | null | undefined
): ComponentType<{ className?: string }> {
  if (!categoryName) {
    return DefaultIcon;
  }

  const normalizedName = categoryName.toLowerCase().trim();

  // Check exact match first
  if (categoryIconMap[normalizedName]) {
    return categoryIconMap[normalizedName];
  }

  // Check partial matches
  for (const [key, icon] of Object.entries(categoryIconMap)) {
    if (normalizedName.includes(key) || key.includes(normalizedName)) {
      return icon;
    }
  }

  return DefaultIcon;
}
