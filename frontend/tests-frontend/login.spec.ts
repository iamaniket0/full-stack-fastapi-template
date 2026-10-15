import { expect, test } from "./fixtures"

test.beforeEach(async ({ page }) => {
  await page.goto("/login")
})

test("Renders the login form", async ({ page }) => {
  await expect(
    page.getByRole("heading", { name: "Login to your account" }),
  ).toBeVisible()
  await expect(page.getByTestId("email-input")).toBeEditable()
  await expect(page.getByTestId("password-input")).toBeEditable()
  await expect(page.getByRole("button", { name: "Log In" })).toBeVisible()
  await expect(
    page.getByRole("link", { name: "Forgot your password?" }),
  ).toBeVisible()
})

test("Shows client-side validation errors", async ({ page }) => {
  await page.getByTestId("email-input").fill("invalidemail")
  await page.getByTestId("password-input").fill("short")
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Invalid email address")).toBeVisible()
  await expect(
    page.getByText("Password must be at least 8 characters"),
  ).toBeVisible()
})

test("Logs in and lands on the dashboard", async ({ page, api }) => {
  await page.getByTestId("email-input").fill(api.user.email)
  await page.getByTestId("password-input").fill(api.validPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")
  await expect(page.getByText(`Hi, ${api.user.full_name}`)).toBeVisible()
  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
})

test("Shows API error on wrong password", async ({ page, api }) => {
  await page.getByTestId("email-input").fill(api.user.email)
  await page.getByTestId("password-input").fill("wrongpassword")
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Incorrect email or password")).toBeVisible()
  await expect(page).toHaveURL("/login")
})

test("Navigates to sign up and password recovery", async ({ page }) => {
  await page.getByRole("link", { name: "Sign up" }).click()
  await expect(page).toHaveURL("/signup")

  await page.goto("/login")
  await page.getByRole("link", { name: "Forgot your password?" }).click()
  await expect(page).toHaveURL("/recover-password")
})
