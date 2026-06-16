import { defineConfig, devices } from "@playwright/test";

/**
 * E2E smoke tests. Assumes the stack is already running
 * (`make api` + `make dev-frontend`). Not run in CI by default.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
