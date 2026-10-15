import { expect, test } from "@playwright/test"

const apiUrl = process.env.VITE_API_URL

test.use({ storageState: { cookies: [], origins: [] } })

test("Ping endpoint returns pong without authentication", async ({
  request,
}) => {
  const response = await request.get(`${apiUrl}/api/v1/utils/ping/`)

  expect(response.status()).toBe(200)
  expect(await response.json()).toEqual({ message: "pong" })

  const postResponse = await request.post(`${apiUrl}/api/v1/utils/ping/`)
  expect(postResponse.status()).toBe(405)
})
