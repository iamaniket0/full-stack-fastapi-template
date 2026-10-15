import { expect, test } from "./fixtures"

test("Unauthenticated users are redirected to /login", async ({ page }) => {
  await page.goto("/settings")
  await page.waitForURL("/login")
})

test("Invalid token is cleared and user is sent to /login", async ({
  page,
  api,
}) => {
  await api.logIn("invalid_token")
  await page.goto("/")
  await page.waitForURL("/login")
  expect(
    await page.evaluate(() => localStorage.getItem("access_token")),
  ).toBeNull()
})

test("Logged-in users visiting /login are redirected home", async ({
  page,
  api,
}) => {
  await api.logIn()
  await page.goto("/login")
  await page.waitForURL("/")
})

test("Log out returns to /login", async ({ page, api }) => {
  await page.goto("/login")
  await page.getByTestId("email-input").fill(api.user.email)
  await page.getByTestId("password-input").fill(api.validPassword)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")

  await page.goto("/settings")
  await page.waitForURL("/login")
})
