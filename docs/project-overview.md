# Project overview

**Squint** is an eval-driven, production-oriented implementation of **agentic Retrieval-Augmented Generation (RAG)**. The product promise is verifiability: answers cite the exact source chunk, the agent's reasoning is visible while it runs, and quality is scored by an automated gate. It is not a chatbot tutorial — it demonstrates how to build a document Q&A product with a stateful LangGraph agent, async indexing, shared domain boundaries, automated evaluation, and hooks for EU regulatory readiness.

For the product-level view (what it does, who buys into it, which use cases it fits), see the root [README](../README.md). This document covers the engineering rationale.

## What problem it solves

Teams building RAG systems often end up with:

- A thin “upload PDF → ask LLM” demo with no guardrails or tests
- Retrieval logic duplicated across API and agent services
- Heavy indexing blocking HTTP request paths
- No structured way to measure retrieval quality or answer faithfulness

This repository shows an alternative: **vertical service slices**, a **shared retrieval domain library**, **Celery-only write paths**, **SSE streaming chat**, and an **eval pipeline** (**DeepEval** live gate + **LangSmith** prod tracing).

## Core capabilities

| Capability | Implementation |
|------------|----------------|
| Document ingest | Presigned MinIO upload → Postgres metadata → Celery indexing job |
| Semantic indexing | PDF chunking + embedding → Qdrant (indexing worker only) |
| Agentic chat | LangGraph: `plan → guard → rewrite → retrieve → generate` with checkpointing |
| Retrieval | Shared `domains/retrieval` lib — API REST + chat in-process (see [ADR 001](adr/001-why-mcp-boundary.md)) |
| Guardrails | PII redaction, prompt-injection detection (chat guard node) |
| Auth | Keycloak JWT / API key / none; RBAC (`admin`, `read`, `write`); tenant scoping |
| Admin | Keycloak Organizations — tenants and users |
| Quality | Per-project unit tests + coverage gates (packages ≥ 80%, services ≥ 70%); API Gherkin (`tests/api`, live — [ADR 004](adr/004-no-in-service-integration-tests.md), [ADR 007](adr/007-no-live-tests-in-ci.md)); Playwright E2E locally (`make e2e`); **DeepEval** live gate; **LangSmith** traces |
| Compliance prep | Shared `core/compliance` protocols (GDPR, NIS2, EU AI Act hooks) — see [Compliance readiness](compliance.md) |

## Architecture (Phase 1)

See **[Architecture](architecture.md)** for C4-style diagrams (system context, containers, LangGraph workflow, indexing sequence), service ports, and chunking/retrieval defaults.

Services:

- **api** — documents, jobs, retrieval, annotations
- **chat** — agent workflow, SSE streaming
- **indexing** — async PDF indexing (never sync in API)
- **admin** — tenant/user administration
- **packages/shared** — domain logic, integrations, auth, compliance hooks, backend i18n ([ADR 006](adr/006-backend-i18n.md))
- **packages/ui-core** — AppShell and shared React chrome ([ADR 005](adr/005-shared-ui-core-appshell.md))

## Design principles

1. **One slice per change** — each feature is a vertical module (`router`, `service`, `providers`, `settings`).
2. **Protocols over concrete types** — repositories and clients are `@runtime_checkable` Protocols; Dishka wires implementations.
3. **Settings in three tiers** — integration `EnvSettings`, service `AppSettings`, module `ModuleSettings` ([ADR 002](adr/002-service-and-module-settings.md)).
4. **Eval-driven** — **DeepEval** live gate (`make eval-live`, manual — [ADR 007](adr/007-no-live-tests-in-ci.md)) and **LangSmith** for prod traceability.
5. **Compliance by extension** — GDPR / NIS2 / EU AI Act hooks live in `core/compliance`; services opt in via ports, not hard-coded SIEM tools.

## Who is this for?

- **Engineers** evaluating agentic RAG architecture patterns
- **Teams** needing a runnable baseline before product hardening
- **Reviewers** (hiring, architecture review) looking for depth beyond a LangChain notebook

## What this is not

- A hosted SaaS product
- A no-code workflow tool (compare: n8n can prototype simple RAG; this repo targets product-grade engineering)
- A complete certified compliance solution (see [compliance.md](compliance.md) for current readiness and roadmap)

## Quick start

See the root [README](../README.md):

```bash
cp .env.example .env
make up-ui      # dev without Keycloak
make up-auth    # full stack with Keycloak + Traefik
```

## Further reading

- [Documentation index](README.md)
- [Architecture](architecture.md)
- [Compliance readiness](compliance.md)
- [ADR 001 — Retrieval boundary](adr/001-why-mcp-boundary.md)
- [ADR 002 — Service settings](adr/002-service-and-module-settings.md)
