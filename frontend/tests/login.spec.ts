import { expect, type Page, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { randomPassword } from "./utils/random.ts"

test.use({ storageState: { cookies: [], origins: [] } })

const fillForm = async (page: Page, email: string, password: string) => {
  await page.getByTestId("email-input").fill(email)
  await page.getByTestId("password-input").fill(password)
}

const verifyInput = async (page: Page, testId: string) => {
  const input = page.getByTestId(testId)
  await expect(input).toBeVisible()
  await expect(input).toHaveText("")
  await expect(input).toBeEditable()
}

test("Inputs are visible, empty and editable", async ({ page }) => {
  await page.goto("/login")

  await verifyInput(page, "email-input")
  await verifyInput(page, "password-input")
})

test("Log In button is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(page.getByRole("button", { name: "Log In" })).toBeVisible()
})

test("Forgot Password link is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(
    page.getByRole("link", { name: "Forgot your password?" }),
  ).toBeVisible()
})

test("Log in with valid email and password ", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
})

test("Remember me checkbox is visible and checked by default", async ({
  page,
}) => {
  await page.goto("/login")

  const checkbox = page.getByTestId("remember-me-checkbox")
  await expect(checkbox).toBeVisible()
  await expect(checkbox).toBeChecked()
})

test("Log in with remember me stores token persistently", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")

  const tokens = await page.evaluate(() => ({
    local: localStorage.getItem("access_token"),
    session: sessionStorage.getItem("access_token"),
  }))
  expect(tokens.local).not.toBeNull()
  expect(tokens.session).toBeNull()
})

test("Log in without remember me stores token for the session only", async ({
  page,
}) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByTestId("remember-me-checkbox").click()
  await expect(page.getByTestId("remember-me-checkbox")).not.toBeChecked()
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  const tokens = await page.evaluate(() => ({
    local: localStorage.getItem("access_token"),
    session: sessionStorage.getItem("access_token"),
  }))
  expect(tokens.local).toBeNull()
  expect(tokens.session).not.toBeNull()
})

test("Remember me controls whether a new tab stays logged in", async ({
  page,
  context,
}) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByTestId("remember-me-checkbox").click()
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")

  // Session-only login survives a reload but not a fresh tab
  await page.reload()
  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  const sessionTab = await context.newPage()
  await sessionTab.goto("/")
  await sessionTab.waitForURL("/login")
  await sessionTab.close()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")

  await expect(page.getByTestId("remember-me-checkbox")).toBeChecked()
  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")

  const rememberedTab = await context.newPage()
  await rememberedTab.goto("/")
  await expect(
    rememberedTab.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()
})

test("Log in with invalid email", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, "invalidemail", firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Invalid email address")).toBeVisible()
})

test("Log in with invalid password", async ({ page }) => {
  const password = randomPassword()

  await page.goto("/login")
  await fillForm(page, firstSuperuser, password)
  await page.getByRole("button", { name: "Log In" }).click()

  await expect(page.getByText("Incorrect email or password")).toBeVisible()
})

test("Successful log out", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")
})

test("Logged-out user cannot access protected routes", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")

  await expect(
    page.getByText("Welcome back, nice to see you again!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")

  await page.goto("/settings")
  await page.waitForURL("/login")
})

test("Redirects to /login when token is wrong", async ({ page }) => {
  await page.goto("/settings")
  await page.evaluate(() => {
    localStorage.setItem("access_token", "invalid_token")
  })
  await page.goto("/settings")
  await page.waitForURL("/login")
  await expect(page).toHaveURL("/login")
})

test.describe("Remember me password (browser password manager)", () => {
  const loginAndWait = async (page: Page, remember: boolean) => {
    await page.goto("/login")
    await fillForm(page, firstSuperuser, firstSuperuserPassword)
    if (!remember) {
      await page.getByTestId("remember-me-checkbox").click()
      await expect(page.getByTestId("remember-me-checkbox")).not.toBeChecked()
    }
    await page.getByRole("button", { name: "Log In" }).click()
    await page.waitForURL("/")
    await expect(
      page.getByText("Welcome back, nice to see you again!"),
    ).toBeVisible()
  }

  test("Login form lets the browser offer to save the password", async ({
    page,
  }) => {
    await page.goto("/login")

    const form = page.locator("form").filter({
      has: page.getByTestId("password-input"),
    })
    const email = form.getByTestId("email-input")
    const password = form.getByTestId("password-input")

    await expect(email).toHaveAttribute("autocomplete", "username")
    await expect(password).toHaveAttribute("autocomplete", "current-password")
    await expect(password).toHaveAttribute("type", "password")

    await fillForm(page, firstSuperuser, firstSuperuserPassword)
    await page.getByRole("button", { name: "Log In" }).click()
    await page.waitForURL("/")
    await expect(
      page.getByText("Welcome back, nice to see you again!"),
    ).toBeVisible()
  })

  test("Login fields are marked so the browser can fill in saved credentials", async ({
    page,
  }) => {
    await page.goto("/login")

    const email = page.getByTestId("email-input")
    const password = page.getByTestId("password-input")

    await expect(email).toHaveAttribute("type", "email")
    await expect(email).toHaveAttribute("name", "username")
    await expect(email).toHaveAttribute("autocomplete", "username")
    await expect(password).toHaveAttribute("name", "password")
    await expect(password).toHaveAttribute("autocomplete", "current-password")
  })

  test("Remember me checkbox is labelled and checked by default", async ({
    page,
  }) => {
    await page.goto("/login")

    const checkbox = page.getByRole("checkbox", { name: "Remember me" })
    await expect(checkbox).toBeVisible()
    await expect(checkbox).toBeChecked()
  })

  test("Remembered login survives closing and reopening the browser", async ({
    page,
    context,
    browser,
  }) => {
    await loginAndWait(page, true)

    // A browser restart keeps localStorage/cookies but drops sessionStorage
    const savedState = await context.storageState()
    await context.close()

    const reopened = await browser.newContext({
      baseURL: test.info().project.use.baseURL,
      storageState: savedState,
    })
    const newPage = await reopened.newPage()
    await newPage.goto("/")
    await expect(
      newPage.getByText("Welcome back, nice to see you again!"),
    ).toBeVisible()
    await expect(newPage).toHaveURL("/")
    await reopened.close()
  })

  test("Login without remember me shows the login page in a new browser session", async ({
    page,
    context,
    browser,
  }) => {
    await loginAndWait(page, false)

    const savedState = await context.storageState()
    await context.close()

    const reopened = await browser.newContext({
      baseURL: test.info().project.use.baseURL,
      storageState: savedState,
    })
    const newPage = await reopened.newPage()
    await newPage.goto("/")
    await newPage.waitForURL("/login")
    await expect(newPage.getByTestId("email-input")).toBeVisible()
    await reopened.close()
  })

  test("Wrong password shows an error and the user stays logged out", async ({
    page,
  }) => {
    await page.goto("/login")
    await fillForm(page, firstSuperuser, randomPassword())
    await page.getByRole("button", { name: "Log In" }).click()

    await expect(page.getByText("Incorrect email or password")).toBeVisible()
    await expect(page).toHaveURL("/login")

    const tokens = await page.evaluate(() => ({
      local: localStorage.getItem("access_token"),
      session: sessionStorage.getItem("access_token"),
    }))
    expect(tokens.local).toBeNull()
    expect(tokens.session).toBeNull()

    await page.goto("/")
    await page.waitForURL("/login")
  })

  for (const remember of [true, false]) {
    test(`Plain-text password is not stored in the browser (remember me ${
      remember ? "checked" : "not checked"
    })`, async ({ page, context }) => {
      await loginAndWait(page, remember)

      const storage = await page.evaluate(() => {
        const dump = (s: Storage) =>
          Array.from({ length: s.length }, (_, i) => {
            const key = s.key(i) ?? ""
            return `${key}=${s.getItem(key) ?? ""}`
          }).join("\n")
        return {
          local: dump(localStorage),
          session: dump(sessionStorage),
          documentCookie: document.cookie,
        }
      })
      const cookies = await context.cookies()

      expect(storage.local).not.toContain(firstSuperuserPassword)
      expect(storage.session).not.toContain(firstSuperuserPassword)
      expect(storage.documentCookie).not.toContain(firstSuperuserPassword)
      for (const cookie of cookies) {
        expect(cookie.name).not.toContain(firstSuperuserPassword)
        expect(decodeURIComponent(cookie.value)).not.toContain(
          firstSuperuserPassword,
        )
      }
    })
  }
})
