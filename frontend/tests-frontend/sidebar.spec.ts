import { expect, test } from "./fixtures"

test.beforeEach(async ({ api }) => {
  await api.logIn()
})

test("Regular users do not see the Admin link", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByRole("link", { name: "Items" })).toBeVisible()
  await expect(page.getByRole("link", { name: "Admin" })).toHaveCount(0)
})

test("Superusers see the Admin link", async ({ page, api }) => {
  api.user.is_superuser = true
  await page.goto("/")
  await expect(page.getByRole("link", { name: "Admin" })).toBeVisible()
})

test("Dashboard falls back to email when full name is missing", async ({
  page,
  api,
}) => {
  api.user.full_name = null
  await page.goto("/")
  await expect(page.getByText(`Hi, ${api.user.email}`)).toBeVisible()
})
