import { HelpCircle } from "lucide-react";
import { getCategoryIcon } from "@/lib/categoryIcons";
import type { Category } from "@/app/types/transactions";

interface CategoryBadgeProps {
  category?: Category | null;
}

export function CategoryBadge({ category }: CategoryBadgeProps) {
  if (!category) {
    const Icon = HelpCircle;
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
        <Icon className="w-3.5 h-3.5" />
        <span>Uncategorized</span>
      </span>
    );
  }

  const Icon = getCategoryIcon(category.name);

  // Use neutral gray color scheme for all categories
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
      <Icon className="w-3.5 h-3.5 text-gray-600" />
      <span>{category.name}</span>
    </span>
  );
}
