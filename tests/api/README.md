# API acceptance (Playwright-BDD + generated OpenAPI)

Black-box HTTP against **running** api / chat / admin. Scenarios are Gherkin; steps may call services **only** through clients typed from `openapi/*.yaml` (`openapi-typescript` + `openapi-fetch`). No Python service imports, no ad-hoc URLs outside those clients.

Not in default CI — needs `make up` (or equivalent). Happy path only. This suite is the HTTP acceptance layer instead of in-service Python integration tests ([ADR 004](../../docs/adr/004-no-in-service-integration-tests.md)).

## Prerequisites

1. Committed specs: `openapi/api.yaml`, `openapi/chat.yaml`, `openapi/admin.yaml` (`make generate-openapi`).
2. Stack up: `make up` (api `:8000`, chat `:8002`, admin `:8003`). Tenant/user list needs Keycloak (`make up-auth`).
3. Copy env: `cp .env.example .env`

## Quick start

```bash
cd tests/api
cp .env.example .env
npm install
npm test
```

From repo root: `make test-api`.

## Features

| File | Journey |
|------|---------|
| `01_health.feature` | `GET /health` on api, chat, admin |
| `02_documents.feature` | `GET /v1/documents` envelope (`items`, `total`) |
| `03_chat_sessions.feature` | create session, then list includes it |
| `04_admin.feature` | `GET /v1/tenants` and `GET /v1/users` envelopes |

## Generated types

`npm run generate:api` writes `src/generated/` from the YAML specs. That directory is gitignored; `postinstall` regenerates it.
