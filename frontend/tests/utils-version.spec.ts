import { expect, test } from "@playwright/test"

const apiUrl = process.env.VITE_API_URL

test.use({ storageState: { cookies: [], origins: [] } })

test("Version endpoint returns the app version", async ({ request }) => {
  const response = await request.get(`${apiUrl}/api/v1/utils/version/`)

  expect(response.status()).toBe(200)
  const body = await response.json()
  expect(Object.keys(body)).toEqual(["version"])
  expect(body.version).toMatch(/^\d+\.\d+\.\d+/)

  const postResponse = await request.post(`${apiUrl}/api/v1/utils/version/`)
  expect(postResponse.status()).toBe(405)
})
