import { expect, test } from "@playwright/test"

test.use({ storageState: { cookies: [], origins: [] } })

const apiUrl = process.env.VITE_API_URL

test("Ping endpoint returns ok", async ({ request }) => {
  const response = await request.get(`${apiUrl}/ping`)

  expect(response.status()).toBe(200)
  expect(await response.json()).toEqual({ ok: true })
})

test("Ping endpoint rejects POST", async ({ request }) => {
  const response = await request.post(`${apiUrl}/ping`)

  expect(response.status()).toBe(405)
})
