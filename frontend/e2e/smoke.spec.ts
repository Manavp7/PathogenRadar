import { expect, test } from "@playwright/test";

test("dashboard loads and all four views render", async ({ page }) => {
  await page.goto("/");

  // Brand + live status.
  await expect(page.getByText("PathogenRadar")).toBeVisible();

  // Overview: KPI + heatmap.
  await expect(page.getByText("Districts monitored")).toBeVisible();

  // Kerala view.
  await page.getByRole("button", { name: "Kerala" }).click();
  await expect(page.getByText("District Ranking")).toBeVisible();

  // District view.
  await page.getByRole("button", { name: "District", exact: true }).click();
  await expect(page.getByText(/Why This Risk Score/i)).toBeVisible();

  // Executive view + briefing.
  await page.getByRole("button", { name: "Executive" }).click();
  await expect(page.getByText("Executive Situation Report")).toBeVisible();
  await expect(page.getByText("Minister Briefing")).toBeVisible();
});
