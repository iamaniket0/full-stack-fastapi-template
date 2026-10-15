import { defineConfig, devices } from "@playwright/test"

// Frontend-only E2E suite: every backend call is mocked with `page.route`,
// so these tests run against the Vite dev server alone (no backend, DB or
// mail server required). The full-stack suite lives in `./tests`.
const port = Number(process.env.PLAYWRIGHT_FRONTEND_PORT ?? 5174)
const baseURL = `http://localhost:${port}`

export default defineConfig({
  testDir: "./tests-frontend",
  outputDir: "./test-results-frontend",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI
    ? [["github"], ["html", { outputFolder: "playwright-report-frontend" }]]
    : [["html", { outputFolder: "playwright-report-frontend" }]],
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: `bunx vite --port ${port} --strictPort`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
  },
})
