import { readFile } from "node:fs/promises"
import { type APIRequestContext, expect, test } from "@playwright/test"
import { createUser } from "./utils/privateApi"
import {
  randomEmail,
  randomItemDescription,
  randomItemTitle,
  randomPassword,
} from "./utils/random"
import { logInUser, logOutUser } from "./utils/user"

const CSV_HEADER = "id,title,description,created_at"
const API_URL = process.env.VITE_API_URL

async function createItemsViaApi(
  request: APIRequestContext,
  email: string,
  password: string,
  items: { title: string; description?: string }[],
) {
  const login = await request.post(`${API_URL}/api/v1/login/access-token`, {
    form: { username: email, password },
  })
  expect(login.ok()).toBe(true)
  const { access_token: token } = await login.json()
  for (const item of items) {
    const response = await request.post(`${API_URL}/api/v1/items/`, {
      headers: { Authorization: `Bearer ${token}` },
      data: item,
    })
    expect(response.ok()).toBe(true)
  }
}

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

test("Shows an error and downloads no file when the export fails", async ({
  page,
}) => {
  let downloaded = false
  page.on("download", () => {
    downloaded = true
  })
  await page.route("**/api/v1/items/export", (route) =>
    route.fulfill({ status: 500, json: { detail: "Export failed" } }),
  )

  await page.goto("/items")
  await page.getByRole("button", { name: "Download CSV" }).click()

  await expect(page.getByText("Something went wrong!")).toBeVisible()
  await expect(page.getByText("CSV downloaded successfully")).toHaveCount(0)
  expect(downloaded).toBe(false)
})

test("A superuser's CSV leaves out another user's items", async ({
  page,
  request,
}) => {
  const email = randomEmail()
  const password = randomPassword()
  const otherTitle = randomItemTitle()
  await createUser({ email, password })
  await createItemsViaApi(request, email, password, [{ title: otherTitle }])

  await page.goto("/items")
  const downloadPromise = page.waitForEvent("download")
  await page.getByRole("button", { name: "Download CSV" }).click()
  const download = await downloadPromise

  const content = await readFile(await download.path(), "utf-8")
  expect(content.split("\r\n")[0]).toBe(CSV_HEADER)
  expect(content).not.toContain(otherTitle)
})

test.describe("Download CSV", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Download CSV button sits above the items table", async ({
    page,
    request,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await createItemsViaApi(request, email, password, [
      { title: randomItemTitle() },
    ])
    await logInUser(page, email, password)

    await page.goto("/items")
    const button = page.getByRole("button", { name: "Download CSV" })
    const table = page.getByRole("table")
    await expect(button).toBeVisible()
    await expect(table).toBeVisible()

    const buttonBox = await button.boundingBox()
    const tableBox = await table.boundingBox()
    expect(buttonBox).not.toBeNull()
    expect(tableBox).not.toBeNull()
    expect(buttonBox!.y + buttonBox!.height).toBeLessThanOrEqual(tableBox!.y)
  })

  test("CSV has one row for every item, beyond the first table page", async ({
    page,
    request,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    const titles = Array.from({ length: 12 }, () => randomItemTitle())
    await createItemsViaApi(
      request,
      email,
      password,
      titles.map((title) => ({ title })),
    )
    await logInUser(page, email, password)

    await page.goto("/items")
    const downloadPromise = page.waitForEvent("download")
    await page.getByRole("button", { name: "Download CSV" }).click()
    const download = await downloadPromise

    expect(download.suggestedFilename()).toBe("items.csv")
    const content = await readFile(await download.path(), "utf-8")
    const rows = content.trim().split("\r\n")
    expect(rows[0]).toBe(CSV_HEADER)
    expect(rows).toHaveLength(titles.length + 1)
    for (const title of titles) {
      expect(content).toContain(title)
    }
  })

  test("CSV shows the item's creation time in UTC", async ({
    page,
    request,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    const before = Date.now()
    await createItemsViaApi(request, email, password, [
      { title: randomItemTitle() },
    ])
    const after = Date.now()
    await logInUser(page, email, password)

    await page.goto("/items")
    const downloadPromise = page.waitForEvent("download")
    await page.getByRole("button", { name: "Download CSV" }).click()
    const download = await downloadPromise

    const content = await readFile(await download.path(), "utf-8")
    const rows = content.trim().split("\r\n")
    expect(rows[0]).toBe(CSV_HEADER)
    const createdAt = rows[1].split(",").at(-1) ?? ""
    expect(createdAt).toMatch(/^\d{4}-\d{2}-\d{2}T.*(Z|\+00:00)$/)
    const exported = Date.parse(createdAt)
    expect(exported).toBeGreaterThanOrEqual(before - 60_000)
    expect(exported).toBeLessThanOrEqual(after + 60_000)
  })

  test("Downloads a header-only CSV when the user has no items", async ({
    page,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    await page.goto("/items")
    await expect(page.getByText("You don't have any items yet")).toBeVisible()
    const downloadPromise = page.waitForEvent("download")
    await page.getByRole("button", { name: "Download CSV" }).click()
    const download = await downloadPromise

    expect(download.suggestedFilename()).toBe("items.csv")
    const content = await readFile(await download.path(), "utf-8")
    expect(content.trim().split("\r\n")).toEqual([CSV_HEADER])
  })

  test("CSV keeps a value with line breaks in one quoted cell", async ({
    page,
    request,
  }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    const description = `first, "line"\nsecond ${randomItemDescription()}`
    await createItemsViaApi(request, email, password, [
      { title: randomItemTitle(), description },
    ])
    await logInUser(page, email, password)

    await page.goto("/items")
    const downloadPromise = page.waitForEvent("download")
    await page.getByRole("button", { name: "Download CSV" }).click()
    const download = await downloadPromise

    const content = await readFile(await download.path(), "utf-8")
    const rows = content.trim().split("\r\n")
    expect(rows[0]).toBe(CSV_HEADER)
    expect(rows).toHaveLength(2)
    expect(content).toContain(`"${description.replace(/"/g, '""')}"`)
  })

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
    expect(content.split("\r\n")[0]).toBe(CSV_HEADER)
    expect(content).toContain(title)
    expect(content).toContain(description)
  })

  test("CSV only contains the logged-in user's own items", async ({ page }) => {
    const password = randomPassword()
    const otherEmail = randomEmail()
    const otherTitle = randomItemTitle()
    await createUser({ email: otherEmail, password })
    await logInUser(page, otherEmail, password)
    await page.goto("/items")
    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill(otherTitle)
    await page.getByRole("button", { name: "Save" }).click()
    await expect(page.getByText("Item created successfully")).toBeVisible()
    await logOutUser(page)

    const email = randomEmail()
    const title = randomItemTitle()
    await createUser({ email, password })
    await logInUser(page, email, password)
    await page.goto("/items")
    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill(title)
    await page.getByRole("button", { name: "Save" }).click()
    await expect(page.getByText("Item created successfully")).toBeVisible()

    const downloadPromise = page.waitForEvent("download")
    await page.getByRole("button", { name: "Download CSV" }).click()
    const download = await downloadPromise

    const content = await readFile(await download.path(), "utf-8")
    const rows = content.trim().split("\r\n")
    expect(rows[0]).toBe(CSV_HEADER)
    expect(rows).toHaveLength(2)
    expect(content).toContain(title)
    expect(content).not.toContain(otherTitle)
  })

  test("CSV escapes commas and quotes in item fields", async ({ page }) => {
    const email = randomEmail()
    const password = randomPassword()
    await createUser({ email, password })
    await logInUser(page, email, password)

    const title = randomItemTitle()
    const description = `has, comma and "quotes" ${randomItemDescription()}`
    await page.goto("/items")
    await page.getByRole("button", { name: "Add Item" }).click()
    await page.getByLabel("Title").fill(title)
    await page.getByLabel("Description").fill(description)
    await page.getByRole("button", { name: "Save" }).click()
    await expect(page.getByText("Item created successfully")).toBeVisible()

    const downloadPromise = page.waitForEvent("download")
    await page.getByRole("button", { name: "Download CSV" }).click()
    const download = await downloadPromise

    const content = await readFile(await download.path(), "utf-8")
    const rows = content.trim().split("\r\n")
    expect(rows).toHaveLength(2)
    expect(rows[1]).toMatch(
      new RegExp(
        `^[0-9a-f-]{36},${title},"${description.replace(/"/g, '""')}",[^,]+$`,
      ),
    )
  })
})
