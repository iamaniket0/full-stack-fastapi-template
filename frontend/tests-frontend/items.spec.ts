import { expect, fulfillJson, test } from "./fixtures"

test.beforeEach(async ({ api }) => {
  await api.logIn()
})

test("Lists items returned by the API", async ({ page, api }) => {
  await page.goto("/items")
  await expect(page.getByRole("heading", { name: "Items" })).toBeVisible()
  await expect(page.getByText(api.items[0].title)).toBeVisible()
})

test("Shows empty state when there are no items", async ({ page, api }) => {
  api.items = []
  await page.goto("/items")
  await expect(page.getByText("You don't have any items yet")).toBeVisible()
})

test("Creates an item and refreshes the list", async ({ page }) => {
  await page.goto("/items")
  await page.getByRole("button", { name: "Add Item" }).click()
  await page.getByLabel("Title").fill("Brand new item")
  await page.getByLabel("Description").fill("Created in a mocked test")
  await page.getByRole("button", { name: "Save" }).click()

  await expect(page.getByText("Item created successfully")).toBeVisible()
  await expect(page.getByText("Brand new item")).toBeVisible()
})

test("Requires a title to create an item", async ({ page }) => {
  await page.goto("/items")
  await page.getByRole("button", { name: "Add Item" }).click()
  await page.getByLabel("Title").fill("")
  await page.getByRole("button", { name: "Save" }).click()

  await expect(page.getByText("Title is required")).toBeVisible()
})

test("Surfaces API errors as a toast", async ({ page, api }) => {
  await api.on("POST", /\/api\/v1\/items\/$/, (route) =>
    fulfillJson(route, { detail: "Something broke on the server" }, 500),
  )
  await page.goto("/items")
  await page.getByRole("button", { name: "Add Item" }).click()
  await page.getByLabel("Title").fill("Doomed item")
  await page.getByRole("button", { name: "Save" }).click()

  await expect(page.getByText("Something broke on the server")).toBeVisible()
})
