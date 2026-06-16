import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import RiskTable from "./RiskTable";
import type { RiskAssessment } from "../api/types";

function mk(id: string, name: string, risk: number, level: RiskAssessment["level"]): RiskAssessment {
  return {
    district_id: id,
    district_name: name,
    date: "2024-03-20",
    risk_score: risk,
    level,
    category: "Vector",
    likely_diseases: [],
    confidence: 0.9,
    signal_scores: {},
    contributions: [],
  };
}

const RISK = [
  mk("a", "Alpha", 20, "Watch"),
  mk("b", "Bravo", 80, "Emergency"),
  mk("c", "Charlie", 5, "Normal"),
];

describe("RiskTable", () => {
  it("sorts districts by risk descending", () => {
    render(<RiskTable risk={RISK} />);
    const rows = screen.getAllByRole("row").slice(1); // skip header
    expect(rows[0]).toHaveTextContent("Bravo");
    expect(rows[2]).toHaveTextContent("Charlie");
  });

  it("respects the limit", () => {
    render(<RiskTable risk={RISK} limit={1} />);
    expect(screen.getAllByRole("row")).toHaveLength(2); // header + 1
  });

  it("fires onSelect on row click", () => {
    const onSelect = vi.fn();
    render(<RiskTable risk={RISK} onSelect={onSelect} />);
    fireEvent.click(screen.getByText("Bravo"));
    expect(onSelect).toHaveBeenCalledWith("b");
  });

  it("hides category for Normal districts", () => {
    render(<RiskTable risk={[mk("c", "Charlie", 5, "Normal")]} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});
