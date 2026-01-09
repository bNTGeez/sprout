import type { Category } from "@/app/types/transactions";

interface CategoryBadgeProps {
  category?: Category | null;
}

export function CategoryBadge({ category }: CategoryBadgeProps) {
  if (!category) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
        <span>❓</span>
        <span>Uncategorized</span>
      </span>
    );
  }

  const backgroundColor = category.color || "#9CA3AF";
  const textColor = getContrastColor(backgroundColor);

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
      style={{
        backgroundColor,
        color: textColor,
      }}
    >
      {category.icon && <span>{category.icon}</span>}
      <span>{category.name}</span>
    </span>
  );
}

// Helper to determine if text should be light or dark based on background
function getContrastColor(hexColor: string): string {
  // Remove # if present
  const hex = hexColor.replace("#", "");

  // Convert to RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Calculate relative luminance
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;

  // Return dark text for light backgrounds, light text for dark backgrounds
  return luminance > 0.5 ? "#1F2937" : "#FFFFFF";
}
