import { readFile } from "node:fs/promises"
import { expect, test } from "@playwright/test"
import { createUser } from "./utils/privateApi"
import {
  randomEmail,
  randomItemDescription,
  randomItemTitle,
  randomPassword,
} from "./utils/random"
import { logInUser } from "./utils/user"

test("Download CSV button is visible on the dashboard after login", async ({
  page,
}) => {
  await page.goto("/")
  await expect(page.getByRole("button", { name: "Download CSV" })).toBeVisible()
})

test("Download CSV button is visible on the items page", async ({ page }) => {
  await page.goto("/items")
  await expect(page.getByRole("button", { name: "Download CSV" })).toBeVisible()
})

test.describe("Download CSV", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Downloads the user's items as a CSV file", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    const title = randomItemTitle()
    const description = randomItemDescription()
    await page.goto("/items")
    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill(title)
    await page.getByLabel("Description").fill(description)
    await page.getByRole("button", { name: "Save" }).click()
    await expect(page.getByText("Item created successfully")).toBeVisible()

    const downloadPromise = page.waitForEvent("download")
    await page.getByRole("button", { name: "Download CSV" }).click()
    const download = await downloadPromise

    expect(download.suggestedFilename()).toBe("items.csv")
    const path = await download.path()
    const content = await readFile(path, "utf-8")
    expect(content.split("\r\n")[0]).toBe("id,title,description")
    expect(content).toContain(title)
    expect(content).toContain(description)
  })
})
