import { expect, test } from "@playwright/test"

const apiUrl = process.env.VITE_API_URL

test.use({ storageState: { cookies: [], origins: [] } })

test("Time endpoint returns current server time in ISO format", async ({
  request,
}) => {
  const before = Date.now()
  const response = await request.get(`${apiUrl}/api/v1/utils/time/`)
  const after = Date.now()

  expect(response.status()).toBe(200)
  const body = await response.json()
  expect(body.time).toMatch(
    /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/,
  )
  const serverTime = Date.parse(body.time)
  expect(serverTime).toBeGreaterThanOrEqual(before - 5000)
  expect(serverTime).toBeLessThanOrEqual(after + 5000)

  const postResponse = await request.post(`${apiUrl}/api/v1/utils/time/`)
  expect(postResponse.status()).toBe(405)
})
