# ADR 004: No in-service Python integration tests

## Context

Each Python service (`api`, `chat`, `admin`, `indexing`) already has fast
`tests/unittest` in CI. We previously also kept in-service HTTP/OpenAPI
integration tests (Schemathesis-style). Those duplicated the published
contract, needed a running stack, and slowed the per-service CI matrix.

The HTTP surface is already specified in committed `openapi/*.yaml` and
exercised from `tests/api` (Playwright-BDD, generated `openapi-fetch`
clients, live services).

## Decision

- **In-service tests are unit tests only** — no `tests/integration/` under
  `services/*` or `packages/shared`.
- **Process-level HTTP acceptance lives in `tests/api`** — black-box calls
  against running api/chat/admin, using only clients generated from
  `openapi/*.yaml`. `make test-api`; not in default CI.
- **UI journeys stay in `tests/e2e`**. RAG quality stays in `tests/eval`.
- **Indexing** has no HTTP API; coverage is unit tests plus the live stack
  (upload → Celery) when `tests/api` / e2e grow that path.

## Consequences

- Service CI stays fast and hermetic (no Postgres/Qdrant/Keycloak in the
  unit job).
- Contract drift is caught where the contract is published (`openapi/` +
  `tests/api`), not by importing FastAPI apps inside pytest.
- `tests/api` is currently happy-path only and requires `make up`. It does
  not replace unit tests, DeepEval, or a full auth/error/SSE matrix.
- Expanding HTTP coverage means adding Gherkin in `tests/api`, not new
  pytest integration suites under services.
