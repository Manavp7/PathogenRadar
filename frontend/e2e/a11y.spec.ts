import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("Overview has no critical accessibility violations", async ({ page }) => {
  await page.goto("/");
  await page.waitForTimeout(1500);
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  const critical = results.violations.filter((v) => v.impact === "critical");
  expect(critical, JSON.stringify(critical.map((v) => v.id))).toEqual([]);
});
