import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { GoalBadge } from "../GoalBadge";
import type { GoalInTransaction } from "@/app/types/transactions";

describe("GoalBadge", () => {
  it("renders nothing when goal is null", () => {
    const { container } = render(<GoalBadge goal={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders goal badge with goal name", () => {
    const goal: GoalInTransaction = {
      id: 1,
      name: "Emergency Fund",
    };

    render(<GoalBadge goal={goal} />);
    
    // Text may be split by whitespace, so use regex
    expect(screen.getByText(/Emergency Fund/)).toBeInTheDocument();
    expect(screen.getByText(/🎯/)).toBeInTheDocument();
  });

  it("has correct styling", () => {
    const goal: GoalInTransaction = {
      id: 1,
      name: "Vacation",
    };

    const { container } = render(<GoalBadge goal={goal} />);
    const badge = container.querySelector("span");
    
    expect(badge).toHaveClass("bg-blue-100", "text-blue-800");
  });
});
