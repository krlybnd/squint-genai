# ADR 006: Backend i18n for server-emitted copy

## Context

The React apps already translate chrome via `@are/ui-core` i18n. That cannot
cover strings the **Python services emit**:

- Chat **SSE** reasoning, guard/block answers, session titles, stream errors
- Annotation **rejection reasons** and locale-specific moderation prompts
- Index job messages **persisted as keys** (e.g. user cancel) and translated on read

Hardcoding English in nodes/routers would freeze the product to one language.
Sending only message keys over SSE would require the frontend to duplicate
the same catalog and stay in lockstep with every graph node.

## Decision

- **`agentic_shared/core/i18n`** — `resolve_locale(Accept-Language)` (`en` /
  `hu` / `de`, default `en`); `t(key, locale)` and `t_stored` over JSON in
  `agentic_shared/locales/messages/`.
- **Translate at the producer:** chat graph/SSE, annotation graph, job status
  read path. Shared catalog so api and chat do not fork strings.
- **`t_stored`:** persist catalog keys in the DB; pass through free-text
  worker errors unchanged.
- **Not gettext/Babel.** Thin JSON flatten + placeholders. Frontend catalogs
  stay separate (UI chrome vs server-emitted copy).

REST `detail` on domain errors may remain English; that is not the SSE/LLM
prompt path.

## Consequences

- User-visible agent copy follows `Accept-Language` without a second client
  catalog for every reasoning line.
- Two catalogs (React vs Python) can drift; new locale = new JSON +
  `SUPPORTED_LOCALES`.
- Callers must thread `locale` through graph state / handlers. Missing it
  falls back to English.
