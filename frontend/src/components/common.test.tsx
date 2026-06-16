import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge, RiskBar } from "./common";

describe("Badge", () => {
  it("renders the level with its class", () => {
    const { container } = render(<Badge level="Emergency" />);
    expect(screen.getByText("Emergency")).toBeInTheDocument();
    expect(container.querySelector(".lvl-Emergency")).toBeTruthy();
  });
});

describe("RiskBar", () => {
  it("clamps width to 100%", () => {
    const { container } = render(<RiskBar risk={150} />);
    const fill = container.querySelector(".riskbar > span") as HTMLElement;
    expect(fill.style.width).toBe("100%");
  });
});
