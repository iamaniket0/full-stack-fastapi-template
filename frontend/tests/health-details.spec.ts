import { expect, test } from "@playwright/test"

const apiUrl = process.env.VITE_API_URL

test.use({ storageState: { cookies: [], origins: [] } })

test("Health details endpoint returns status ok and UTC time", async ({
  request,
}) => {
  const response = await request.get(`${apiUrl}/api/v1/health/details`)

  expect(response.status()).toBe(200)
  const body = await response.json()
  expect(body.status).toBe("ok")
  expect(Number.isNaN(Date.parse(body.time))).toBe(false)
  expect(body.time).toMatch(/\+00:00$/)
})
