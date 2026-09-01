# API acceptance (Playwright-BDD + generated OpenAPI)

Black-box HTTP against **running** api / chat / admin. Scenarios are Gherkin; steps may call services **only** through clients typed from `openapi/*.yaml` (`openapi-typescript` + `openapi-fetch`). No Python service imports, no ad-hoc URLs outside those clients. Chat SSE is `text/event-stream` (string body); steps still split `event:` / `data:` frames.

Not in default CI — needs `make up` (or equivalent). Happy path only for smoke features; `@guardrails` needs the classifier profile. This suite is the HTTP acceptance layer instead of in-service Python integration tests ([ADR 004](../../docs/adr/004-no-in-service-integration-tests.md)).

## Prerequisites

1. Committed specs: `openapi/api.yaml`, `openapi/chat.yaml`, `openapi/admin.yaml` (`make generate-openapi`).
2. Stack up: `make up` (api `:8000`, chat `:8002`, admin `:8003`). Tenant/user list and `@auth` / `@me` need Keycloak (`make up-auth`, `AUTH_MODE=jwt`).
3. Copy env: `cp .env.example .env`
4. **Guardrails feature:** `make up-guardrails`, set chat/api `GUARD_API_BASE` / `GUARD_AUTH_TOKEN` (docker DNS or host ports), and have at least one indexed document (or `API_TEST_CHUNK_ID`) for comment scenarios.

## Quick start

```bash
cd tests/api
cp .env.example .env
npm install
npm test
```

From repo root: `make test-api`.

Guardrails only:

```bash
npx playwright test --grep @guardrails
```

JWT auth / caller tenancy only:

```bash
npx playwright test --grep @auth
```

## Features

| File | Journey |
|------|---------|
| `01_health.feature` | `GET /health` on api, chat, admin |
| `02_documents.feature` | `GET /v1/documents` envelope (`items`, `total`) |
| `03_chat_sessions.feature` | create session, then list includes it |
| `04_admin.feature` | `GET /v1/tenants` and `GET /v1/users` envelopes |
| `05_guardrails.feature` | BanSubstrings hard reject (chat SSE + comment 422) + clean pass |
| `06_pii_vault.feature` | Index-time PII tokens in Qdrant + `/vault/detokenize` (@pii-vault) |
| `07_me.feature` | JWT `GET /v1/me` + `PUT /v1/me/active-tenant` without `manage-realm` (`@auth` `@me`; skips if not jwt) |

Banned phrases are defined in `operations/llm-guard/config/scanners.yml` (`BanSubstrings`) and mirrored in `src/guardrails.ts`.

PII vault feature additionally requires:

- `make up-guardrails` (Presidio analyzer for index-time tokenization)
- Indexing worker: `INDEXING_PDF_PII_TOKENIZATION_ENABLED=true` plus shared `VAULT_ENCRYPTION_KEY` / `VAULT_TOKEN_SALT` (same values as API)
- Chat/API: `PII_VAULT_ENABLED=true` for query tokenization + SSE detokenize on chat `done` events
- Alembic revision `003` applied (`make migrate` or ops bootstrap)
- tests/api `.env`: `PII_VAULT_TESTS_ENABLED=true`

## Generated types

`npm run generate:api` writes `src/generated/` from the YAML specs. That directory is gitignored; `postinstall` regenerates it.
