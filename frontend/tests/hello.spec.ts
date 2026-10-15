import { expect, test } from "@playwright/test"

const apiUrl = process.env.VITE_API_URL

test.use({ storageState: { cookies: [], origins: [] } })

test("Hello endpoint returns a greeting", async ({ request }) => {
  const response = await request.get(`${apiUrl}/api/v1/hello`)

  expect(response.status()).toBe(200)
  expect(await response.json()).toEqual({ message: "Hello, World!" })
})

test("Hello endpoint does not require authentication", async ({ request }) => {
  const response = await request.get(`${apiUrl}/api/v1/hello`, {
    headers: { Authorization: "Bearer invalid-token" },
  })

  expect(response.status()).toBe(200)
})
