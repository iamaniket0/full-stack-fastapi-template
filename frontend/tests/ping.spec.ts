import { expect, test } from "@playwright/test"

const apiUrl = process.env.VITE_API_URL

test.use({ storageState: { cookies: [], origins: [] } })

test("Ping endpoint returns ok true", async ({ request }) => {
  const response = await request.get(`${apiUrl}/api/v1/ping`)

  expect(response.status()).toBe(200)
  expect(await response.json()).toEqual({ ok: true })

  const postResponse = await request.post(`${apiUrl}/api/v1/ping`)
  expect(postResponse.status()).toBe(405)
})
