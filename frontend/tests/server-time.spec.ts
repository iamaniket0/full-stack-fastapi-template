import { expect, test } from "@playwright/test"

test("Server Time page is accessible and shows the time", async ({ page }) => {
  await page.goto("/server-time")
  await expect(page.getByRole("heading", { name: "Server Time" })).toBeVisible()
  await expect(page.getByTestId("server-time")).toBeVisible()
  await expect(page.getByTestId("server-time")).toContainText("UTC:")
})

test("Server Time is reachable from the sidebar", async ({ page }) => {
  await page.goto("/")
  await page.getByRole("link", { name: "Server Time" }).click()
  await expect(page).toHaveURL("/server-time")
  await expect(page.getByRole("heading", { name: "Server Time" })).toBeVisible()
})

test("Server Time shows an error when the server time cannot be loaded", async ({
  page,
}) => {
  await page.route("**/api/v1/utils/server-time/", (route) =>
    route.fulfill({ status: 500, body: "Internal Server Error" }),
  )
  await page.goto("/server-time")
  await expect(page.getByText("Could not load the server time.")).toBeVisible({
    timeout: 15_000,
  })
  await expect(page.getByTestId("server-time")).not.toBeVisible()
})

test("Server Time shows the server's time, not the browser's", async ({
  page,
}) => {
  await page.route("**/api/v1/utils/server-time/", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ server_time: "2000-01-01T12:00:00Z" }),
    }),
  )
  await page.goto("/server-time")
  await expect(page.getByTestId("server-time")).toContainText(
    "UTC: 2000-01-01T12:00:0",
  )
})

test("Server Time shows an error when the server time is invalid", async ({
  page,
}) => {
  await page.route("**/api/v1/utils/server-time/", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ server_time: "not-a-date" }),
    }),
  )
  await page.goto("/server-time")
  await expect(page.getByText("Could not load the server time.")).toBeVisible()
  await expect(page.getByTestId("server-time")).not.toBeVisible()
})

test("Server Time matches the real server clock and keeps ticking", async ({
  page,
  request,
}) => {
  const readUtc = async () => {
    const text = await page.getByTestId("server-time").innerText()
    const match = text.match(/UTC: (\S+)/)
    expect(match).not.toBeNull()
    return new Date(match![1]).getTime()
  }

  await page.goto("/server-time")
  await expect(page.getByTestId("server-time")).toBeVisible()

  const apiUrl = process.env.VITE_API_URL ?? "http://localhost:8000"
  const response = await request.get(`${apiUrl}/api/v1/utils/server-time/`)
  expect(response.ok()).toBeTruthy()
  const { server_time } = await response.json()
  const apiTime = new Date(server_time).getTime()

  const shown = await readUtc()
  expect(Math.abs(shown - apiTime)).toBeLessThan(5_000)

  await expect.poll(readUtc, { timeout: 5_000 }).toBeGreaterThan(shown)
})

test.describe("Server Time requires login", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Logged-out user is redirected to login", async ({ page }) => {
    await page.goto("/server-time")
    await expect(page).toHaveURL("/login")
    await expect(page.getByTestId("server-time")).not.toBeVisible()
  })
})
