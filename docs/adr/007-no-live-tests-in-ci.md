# ADR 007: No live-stack tests in default CI

## Context

The repo ships several suites that need a running stack:

- **`tests/api`** — Playwright-BDD HTTP acceptance against live api/chat/admin
- **`tests/e2e`** — browser UI journeys
- **`tests/eval`** — retrieval IR (Pydantic Evals) + generation quality (DeepEval `evaluate()`) against the running chat SSE API

Default CI already runs fast, hermetic jobs: per-project lint, Python unit tests with
coverage gates, Node unit tests, and a merged license/SBOM policy check (see
[ADR 004](004-no-in-service-integration-tests.md)).

Squint is a **demonstration / reference architecture** project — it showcases
patterns (agent graph, retrieval, multitenancy hooks, compliance extension points)
rather than operating as revenue-bearing production software. Running Postgres,
Redis, Qdrant, MinIO, Keycloak, and LLM-backed services on every push would
slow feedback, increase flake and secret-management cost, and duplicate coverage
that unit tests plus optional local suites already provide.

## Decision

- **Default GitHub Actions CI does not start docker-compose or run live-stack suites.**
- **`tests/eval` is not run in CI** — neither the offline dataset smoke (`make -C tests/eval run`) nor the live gate (`make eval-live`). Same rationale as `tests/e2e`: the suite belongs to the live-stack / quality-validation path, not the fast hermetic PR gate ([ADR 004](004-no-in-service-integration-tests.md)).
- **`tests/api`, `tests/e2e`, and `make eval-live` remain manual / on-demand** — documented in root README and `tests/*/README.md`; developers run them after `make up` when validating end-to-end behavior.
- **CI continues to gate** lint, unit coverage (packages ≥ 80%, services ≥ 70%), and license policy.
- **Contract drift** is mitigated by committed `openapi/*.yaml`, generated clients, and local `make test-api` — not by blocking every PR on a full stack.

## Consequences

- PR feedback stays fast and cheap; no CI secrets for LiteLLM/OpenAI keys required on every run.
- Integration regressions (SSE streaming, Celery indexing, Keycloak auth paths) are caught when someone runs live suites locally or in a dedicated demo/staging workflow — not automatically on each commit.
- If the project later becomes production-critical, add an optional CI workflow (nightly or `workflow_dispatch`) that runs `make up` + `tests/api` smoke — without changing the default PR path documented here.
