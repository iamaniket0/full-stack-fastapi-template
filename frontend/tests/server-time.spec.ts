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
