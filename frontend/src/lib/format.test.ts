import { describe, expect, it } from "vitest";
import { fmtInt, fmtPct, levelForRisk, riskColor, shortDate } from "./format";

describe("format utils", () => {
  it("maps risk scores to escalating levels", () => {
    expect(levelForRisk(5)).toBe("Normal");
    expect(levelForRisk(20)).toBe("Watch");
    expect(levelForRisk(40)).toBe("Warning");
    expect(levelForRisk(60)).toBe("Alert");
    expect(levelForRisk(80)).toBe("Emergency");
  });

  it("assigns colours consistent with levels", () => {
    expect(riskColor(80)).toBe(riskColor(90));
    expect(riskColor(5)).not.toBe(riskColor(80));
  });

  it("formats integers and percentages", () => {
    expect(fmtInt(1234.6)).toMatch(/1,235|1235/);
    expect(fmtPct(0.5)).toBe("50%");
    expect(fmtPct(0.123, 1)).toBe("12.3%");
  });

  it("formats short dates", () => {
    expect(shortDate("2024-03-20")).toMatch(/Mar/);
  });
});
