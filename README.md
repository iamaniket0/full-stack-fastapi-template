# Full Stack FastAPI Template

[![Test Docker Compose](../../actions/workflows/test-docker-compose.yml/badge.svg)](../../actions/workflows/test-docker-compose.yml)
[![Test Backend](../../actions/workflows/test-backend.yml/badge.svg)](../../actions/workflows/test-backend.yml)

## About the Project

This is a full stack web application template. It gives you a ready-to-use starting point with a Python API backend, a React frontend, a PostgreSQL database, user authentication, and deployment setup, so you can focus on building your own features.

Out of the box it includes:

- User sign up, login, and password recovery by email.
- An admin dashboard to manage users.
- An example "Items" feature showing how to create, read, update, and delete data.
- Automatically generated, interactive API documentation.

### Project Structure

- `backend/` - FastAPI application (API routes, database models, migrations, and tests).
- `frontend/` - React + TypeScript application built with Vite.
- `packages/react-email/` - Email templates built with React Email.
- `scripts/` - Helper scripts for development and CI.
- `compose*.yml` - Docker Compose files for local services and deployment.

### Quick Start

```bash
# Start the database and local email server
docker compose up -d db mailpit

# Backend (from the backend directory)
uv sync
uv run bash scripts/prestart.sh
uv run fastapi dev

# Frontend (from the project root, in another terminal)
bun install
bun run dev
```

Then open the frontend at <http://localhost:5173> and the API docs at <http://localhost:8000/docs>. See [development.md](./development.md) for more details.

### How It Can Be Improved

Some ideas for taking the project further:

- **Authentication** - add refresh tokens, social login (OAuth), and two-factor authentication.
- **Security** - add rate limiting on login and password recovery endpoints.
- **Background jobs** - move slow tasks like sending emails to a task queue (e.g. Celery or ARQ with Redis).
- **Caching** - cache frequently read data to reduce database load.
- **Observability** - add structured logging and metrics alongside the existing Sentry integration.
- **Internationalization** - support multiple languages in the frontend and email templates.
- **Testing** - increase test coverage, especially for the frontend and edge cases in the API.
- **Documentation** - add architecture diagrams and more examples of extending the data models.

Contributions are welcome, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
  - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
  - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
  - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
- 🚀 [React](https://react.dev) for the frontend.
  - 🧩 Built into the backend application and served by FastAPI on the same domain as the API.
  - 💃 Using TypeScript, hooks, [Vite](https://vitejs.dev), and other parts of a modern frontend stack.
  - 🎨 [Tailwind CSS](https://tailwindcss.com) and [shadcn/ui](https://ui.shadcn.com) for the frontend components.
  - 🤖 An automatically generated frontend client.
  - 🧪 [Playwright](https://playwright.dev) for end-to-end testing.
  - 🦇 Dark mode support.
- ☁️ [FastAPI Cloud](https://fastapicloud.com) for deployment.
- 🐋 [Docker Compose](https://www.docker.com) for local services and self-hosted deployment.
  - 📞 [Traefik](https://traefik.io) as a reverse proxy with automatic HTTPS.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email-based password recovery.
- ✉️ [React Email](https://react.email) for email templates.
- 📬 [Mailpit](https://mailpit.axllent.org) for local email testing during development.
- ✅ Tests with [Pytest](https://pytest.org).
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

### Dashboard Login

![Dashboard login screenshot](img/login.png)

### Dashboard - Admin

![Admin dashboard screenshot](img/dashboard.png)

### Dashboard - Items

![Items dashboard screenshot](img/dashboard-items.png)

### Dashboard - Dark Mode

![Dark mode dashboard screenshot](img/dashboard-dark.png)

### React Email Templates

![Email templates screenshot](img/react-email.png)

### Mailpit - Local Email Testing

![Mailpit screenshot](img/mailpit.png)

### Interactive API Documentation

![API docs](img/docs.png)

## How to Use It

Click the **Use this template** button at the top of this page to create a new repository.

## Backend Development

Backend docs: [backend/README.md](./backend/README.md).

## Frontend Development

Frontend docs: [frontend/README.md](./frontend/README.md).

## Deployment

FastAPI Cloud deployment: [deployment.md](./deployment.md).

Self-hosted deployment with Docker Compose: [deployment-docker-compose.md](./deployment-docker-compose.md).

## Development

General development docs: [development.md](./development.md).

This includes the local FastAPI and Vite workflow, Docker Compose services, `.env` configuration, and more.

## Release Notes

Check the file [release-notes.md](./release-notes.md).

## License

The Full Stack FastAPI Template is licensed under the terms of the MIT license.
