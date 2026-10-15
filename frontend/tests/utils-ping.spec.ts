import { expect, test } from "@playwright/test"

const apiUrl = process.env.VITE_API_URL

test.use({ storageState: { cookies: [], origins: [] } })

test("Ping endpoint returns pong", async ({ request }) => {
  const response = await request.get(`${apiUrl}/api/v1/utils/ping/`)

  expect(response.status()).toBe(200)
  expect(await response.json()).toBe("pong")

  const postResponse = await request.post(`${apiUrl}/api/v1/utils/ping/`)
  expect(postResponse.status()).toBe(405)
})
