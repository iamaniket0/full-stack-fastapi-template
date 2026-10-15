import { expect, test } from "./fixtures"

test.beforeEach(async ({ page }) => {
  await page.goto("/signup")
})

test("Shows validation errors for mismatched passwords", async ({ page }) => {
  await page.getByTestId("full-name-input").fill("New User")
  await page.getByTestId("email-input").fill("new@example.com")
  await page.getByTestId("password-input").fill("changethis123")
  await page.getByTestId("confirm-password-input").fill("different123")
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("The passwords don't match")).toBeVisible()
})

test("Signs up and redirects to /login", async ({ page }) => {
  const request = page.waitForRequest(
    (req) =>
      req.url().endsWith("/api/v1/users/signup") && req.method() === "POST",
  )
  await page.getByTestId("full-name-input").fill("New User")
  await page.getByTestId("email-input").fill("new@example.com")
  await page.getByTestId("password-input").fill("changethis123")
  await page.getByTestId("confirm-password-input").fill("changethis123")
  await page.getByRole("button", { name: "Sign Up" }).click()

  expect((await request).postDataJSON()).toMatchObject({
    email: "new@example.com",
    full_name: "New User",
    password: "changethis123",
  })
  await page.waitForURL("/login")
})
