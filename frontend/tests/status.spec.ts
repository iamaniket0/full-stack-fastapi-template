import { expect, test } from "@playwright/test"

test.use({ storageState: { cookies: [], origins: [] } })

const statusUrl = `${process.env.VITE_API_URL ?? ""}/status`

test("Status endpoint reports healthy", async ({ request }) => {
  const response = await request.get(statusUrl)

  expect(response.status()).toBe(200)
  expect(await response.json()).toEqual({ healthy: true })
})

test("Status endpoint does not require authentication", async ({
  request,
}) => {
  const response = await request.get(statusUrl, {
    headers: { Authorization: "" },
  })

  expect(response.ok()).toBeTruthy()
})
