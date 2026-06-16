import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import Contributions from "./Contributions";

describe("Contributions", () => {
  it("shows an empty state when there are no drivers", () => {
    render(<Contributions items={[]} />);
    expect(screen.getByText(/No significant drivers/i)).toBeInTheDocument();
  });

  it("renders each contribution with its detail", () => {
    render(
      <Contributions
        items={[
          { label: "Fever searches", value: 163.2, detail: "+163.2% vs baseline" },
          { label: "PCR test requests", value: 189.1, detail: "+189.1% vs baseline" },
        ]}
      />
    );
    expect(screen.getByText("Fever searches")).toBeInTheDocument();
    expect(screen.getByText("+189.1% vs baseline")).toBeInTheDocument();
  });
});
