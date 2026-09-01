# API acceptance (Playwright-BDD + generated OpenAPI)

Black-box HTTP against **running** api / chat / admin. Scenarios are Gherkin; steps may call services **only** through clients typed from `openapi/*.yaml` (`openapi-typescript` + `openapi-fetch`). No Python service imports, no ad-hoc URLs outside those clients. Chat SSE is `text/event-stream` (string body); steps still split `event:` / `data:` frames.

Not in default CI — needs a running stack. Happy path only for smoke features; `@guardrails` needs the classifier profile. This suite is the HTTP acceptance layer instead of in-service Python integration tests ([ADR 004](../../docs/adr/004-no-in-service-integration-tests.md)).

## Prerequisites

1. Committed specs: `openapi/api.yaml`, `openapi/chat.yaml`, `openapi/admin.yaml` (`make generate-openapi`).
2. Stack up: auth overlay (Traefik `:80` only) or lab compose (host ports `:8000` / `:8002` / `:8003`) — [`tools/ops/README.md`](../../tools/ops/README.md). Point `.env` at the same origin (see `.env.example`). Tenant/user list and `@auth` / `@me` need Keycloak (`AUTH_MODE=jwt`). Default Playwright fixtures send an admin Bearer when the token endpoint is reachable.
3. Copy env: `cp .env.example .env`
4. **Guardrails feature:** `docker compose --profile guardrails up -d` (add `-f operations/compose.ingress.yaml` when using the auth overlay). Point `GUARD_API_BASE` at `:8010` (host ports) or `http://localhost/guard` (Traefik). Comment scenarios need at least one indexed document (or `API_TEST_CHUNK_ID`).

## Quick start

```bash
cd tests/api
cp .env.example .env
npm install
npm test
```

From repo root: `make system-test` (`test-api` alias).

Guardrails only:

```bash
npx playwright test --grep @guardrails
```

JWT auth / tenant isolation / caller tenancy only:

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
| `07_auth.feature` | JWT 401/403, tenant isolation, spoofed `X-Tenant-Id` (`@auth`; skips if not jwt) |
| `07_me.feature` | JWT `GET /v1/me` + `PUT /v1/me/active-tenant` without `manage-realm` (`@auth` `@me`; skips if not jwt) |
| `08_ai_system_card.feature` | `GET /v1/ai/system-card` envelope |

Banned phrases are defined in `operations/llm-guard/config/scanners.yml` (`BanSubstrings`) and mirrored in `src/guardrails.ts`.

PII vault feature additionally requires:

- `docker compose --profile guardrails up -d` (Presidio analyzer for index-time tokenization)
- Indexing worker: `INDEXING_PDF_PII_TOKENIZATION_ENABLED=true` plus shared `VAULT_ENCRYPTION_KEY` / `VAULT_TOKEN_SALT` (same values as API)
- Chat/API: `PII_VAULT_ENABLED=true` for query tokenization + SSE detokenize on chat `done` events
- Alembic revision `003` applied (`make migrate` or ops bootstrap)
- tests/api `.env`: `PII_VAULT_TESTS_ENABLED=true`

## Generated types

`npm run generate:api` writes `src/generated/` from the YAML specs. That directory is gitignored; `postinstall` regenerates it.
