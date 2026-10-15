import { expect, test } from "@playwright/test"

const apiUrl = process.env.VITE_API_URL

test("Version endpoint returns app version", async ({ request }) => {
  const response = await request.get(`${apiUrl}/api/v1/utils/version/`)

  expect(response.status()).toBe(200)
  const body = await response.json()
  expect(body.version).toBeDefined()
  expect(typeof body.version).toBe("string")
  expect(body.version.length).toBeGreaterThan(0)

  // Test that POST is not allowed (should return 405)
  const postResponse = await request.post(`${apiUrl}/api/v1/utils/version/`)
  expect(postResponse.status()).toBe(405)
})
