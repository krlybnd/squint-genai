# ADR 001: Retrieval domain boundary

## Context

Retrieval logic (LlamaIndex + Qdrant) must be decoupled from the LangGraph agent and
exposed via the API REST surface for the frontend.

Indexing (write path) stays in the Celery indexing service via `indexing-domain`.

## Decision

- **`packages/shared/src/agentic_shared/domains/retrieval`** — `RetrievalService`: search, citation, catalog (Qdrant read + query embed)
- **`packages/shared/src/agentic_shared/domains/indexing`** — semantic chunk + Qdrant upsert (indexing worker)
- **`services/api`** — REST `/v1/retrieval/*` using the shared domain lib
- **`services/chat`** — LangGraph agent calls the same domain lib in-process (no internal HTTP)
- **`services/indexing`** — Celery worker; only write path to Qdrant

## Consequences

- Single source of truth for retrieval (domain lib)
- No duplicated internal HTTP adapter or extra microservice
- Chat and API share `AsyncRetrievalService`; agent tests mock `AsyncRetrievalReader`
- Frontend uses API REST only
