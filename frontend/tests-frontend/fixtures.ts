import { test as base, type Page, type Route } from "@playwright/test"

import type { ItemPublic, UserPublic } from "../src/client"

export const mockUser: UserPublic = {
  id: "00000000-0000-0000-0000-000000000001",
  email: "jane@example.com",
  full_name: "Jane Doe",
  is_active: true,
  is_superuser: false,
  created_at: "2026-01-01T00:00:00Z",
}

export const mockItems: ItemPublic[] = [
  {
    id: "00000000-0000-0000-0000-000000000101",
    title: "First mocked item",
    description: "Served by the mock API",
    owner_id: mockUser.id,
    created_at: "2026-01-01T00:00:00Z",
  },
]

const corsHeaders = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "*",
  "access-control-allow-methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
}

const itemsUrl = /\/api\/v1\/items\/(\?.*)?$/

export const fulfillJson = (route: Route, body: unknown, status = 200) =>
  route.fulfill({ status, json: body, headers: corsHeaders })

/**
 * In-memory fake of the backend API. Each test gets a fresh instance so
 * tests can tweak `user` / `items` or override routes without interfering.
 */
export class MockApi {
  user: UserPublic = { ...mockUser }
  items: ItemPublic[] = mockItems.map((item) => ({ ...item }))
  validPassword = "changethis123"

  constructor(private readonly page: Page) {}

  async install() {
    // Fail loudly on any API call that isn't explicitly mocked
    await this.page.route("**/api/v1/**", (route) => {
      if (route.request().method() === "OPTIONS") {
        return route.fulfill({ status: 204, headers: corsHeaders })
      }
      return fulfillJson(
        route,
        { detail: `Unmocked request: ${route.request().url()}` },
        501,
      )
    })

    await this.on("POST", "**/api/v1/login/access-token", (route) => {
      const form = new URLSearchParams(route.request().postData() ?? "")
      if (
        form.get("username") === this.user.email &&
        form.get("password") === this.validPassword
      ) {
        return fulfillJson(route, {
          access_token: "mock-token",
          token_type: "bearer",
        })
      }
      return fulfillJson(route, { detail: "Incorrect email or password" }, 400)
    })

    await this.on("GET", "**/api/v1/users/me", (route) => {
      const auth = route.request().headers().authorization
      if (auth !== "Bearer mock-token") {
        return fulfillJson(route, { detail: "Could not validate" }, 403)
      }
      return fulfillJson(route, this.user)
    })

    await this.on("POST", "**/api/v1/users/signup", (route) => {
      const body = route.request().postDataJSON()
      return fulfillJson(route, {
        ...mockUser,
        id: "00000000-0000-0000-0000-000000000002",
        email: body.email,
        full_name: body.full_name,
      })
    })

    await this.on("GET", itemsUrl, (route) =>
      fulfillJson(route, { data: this.items, count: this.items.length }),
    )

    await this.on("POST", itemsUrl, (route) => {
      const body = route.request().postDataJSON()
      const item: ItemPublic = {
        id: `00000000-0000-0000-0000-${String(this.items.length + 200).padStart(12, "0")}`,
        title: body.title,
        description: body.description ?? null,
        owner_id: this.user.id,
        created_at: new Date().toISOString(),
      }
      this.items.push(item)
      return fulfillJson(route, item)
    })
  }

  /** Register a handler for a single method + URL pattern. */
  async on(
    method: string,
    url: string | RegExp,
    handler: (route: Route) => Promise<void> | void,
  ) {
    await this.page.route(url, (route) => {
      if (route.request().method() !== method) return route.fallback()
      return handler(route)
    })
  }

  /** Seed a token so protected routes render without going through /login. */
  async logIn(token = "mock-token") {
    // Only seed once per tab so later logouts / token clears are respected
    await this.page.addInitScript((value) => {
      if (!sessionStorage.getItem("mock-token-seeded")) {
        localStorage.setItem("access_token", value)
        sessionStorage.setItem("mock-token-seeded", "1")
      }
    }, token)
  }
}

export const test = base.extend<{ api: MockApi }>({
  // `auto` so the backend is mocked even in tests that don't use `api`
  api: [
    async ({ page }, use) => {
      const api = new MockApi(page)
      await api.install()
      await use(api)
    },
    { auto: true },
  ],
})

export { expect } from "@playwright/test"
