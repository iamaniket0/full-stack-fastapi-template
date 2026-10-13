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
