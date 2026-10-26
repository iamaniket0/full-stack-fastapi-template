import { expect, type Page, test } from "@playwright/test"
import { createUser } from "./utils/privateApi"
import { randomEmail, randomItemTitle, randomPassword } from "./utils/random"
import { logInUser } from "./utils/user"

async function addItem(page: Page, title: string) {
  await page.getByRole("button", { name: "Add Item" }).click()
  await page.getByLabel("Title").fill(title)
  await page.getByRole("button", { name: "Save" }).click()
  await expect(page.getByText("Item created successfully")).toBeVisible()
  await expect(page.getByRole("dialog")).not.toBeVisible()
}

async function openActions(page: Page, title: string) {
  const itemRow = page.getByRole("row").filter({ hasText: title })
  await itemRow.getByRole("button").last().click()
}

test("Show archived toggle is visible on the items page", async ({ page }) => {
  await page.goto("/items")
  await expect(page.getByLabel("Show archived")).toBeVisible()
})

test.describe("Archive items", () => {
  test.use({ storageState: { cookies: [], origins: [] } })
  let email: string
  const password = randomPassword()

  test.beforeAll(async () => {
    email = randomEmail()
    await createUser({ email, password })
  })

  test.beforeEach(async ({ page }) => {
    await logInUser(page, email, password)
    await page.goto("/items")
  })

  test("Archiving an item hides it with a success message", async ({
    page,
  }) => {
    const keptTitle = randomItemTitle()
    const title = randomItemTitle()
    await addItem(page, keptTitle)
    await addItem(page, title)

    await openActions(page, title)
    await page.getByRole("menuitem", { name: "Archive", exact: true }).click()

    await expect(page.getByText(/archived successfully/i)).toBeVisible()
    await expect(page.getByRole("row").filter({ hasText: title })).toHaveCount(
      0,
    )
    await expect(
      page.getByRole("row").filter({ hasText: keptTitle }),
    ).toBeVisible()
  })

  test("Show archived lists archived items with a badge and Unarchive action", async ({
    page,
  }) => {
    const title = randomItemTitle()
    await addItem(page, title)
    await openActions(page, title)
    await page.getByRole("menuitem", { name: "Archive", exact: true }).click()
    await expect(page.getByText(/archived successfully/i)).toBeVisible()

    await page.getByLabel("Show archived").click()

    const itemRow = page.getByRole("row").filter({ hasText: title })
    await expect(itemRow).toBeVisible()
    await expect(itemRow.getByText("Archived", { exact: true })).toBeVisible()

    await itemRow.getByRole("button").last().click()
    await expect(
      page.getByRole("menuitem", { name: "Unarchive", exact: true }),
    ).toBeVisible()
  })

  test("Unarchiving an item brings it back to the default list", async ({
    page,
  }) => {
    const title = randomItemTitle()
    await addItem(page, title)
    await openActions(page, title)
    await page.getByRole("menuitem", { name: "Archive", exact: true }).click()
    await expect(page.getByText(/archived successfully/i)).toBeVisible()

    await page.getByLabel("Show archived").click()
    await openActions(page, title)
    await page.getByRole("menuitem", { name: "Unarchive", exact: true }).click()
    await expect(page.getByText(/unarchived successfully/i)).toBeVisible()

    await page.getByLabel("Show archived").click()
    const itemRow = page.getByRole("row").filter({ hasText: title })
    await expect(itemRow).toBeVisible()
    await expect(itemRow.getByText("Archived", { exact: true })).toHaveCount(0)
  })
})
