# ADR 009: Soft multi-tenancy in Phase 1 auth

## Context

Phase 1 persists `tenant_id` on entities and resolves it from JWT / `X-Tenant-Id`
(Keycloak Organizations demo). Full multitenancy product features (hard isolation,
billing, per-tenant infra) are Phase 2 ([project scope](../../.cursor/rules/00-project-scope.mdc)).

Auth also supports several inbound modes (`jwt`, `api_key`, `none`, plus internal
service key) so local demos and service-to-service calls work without a full IdP.

## Decision

- **Soft tenancy:** shared database / collections; row-level `tenant_id` filtering via
  `AuthContext` + `resolve_tenant_id`. Not separate DB/schema per tenant.
- **Identity lives in** `agentic_shared.crosscut.auth` (framework-free): `AuthContext`,
  `AuthService`, typed `AccessTokenClaims` / `TenantRolesMap`, `JwtValidator`.
- **HTTP/Dishka wiring lives in** `agentic_shared.frameworks.fastapi.providers.auth`
  (`AuthProvider`) and `dependencies.auth` (`require_roles`) — Starlette `Request` /
  `HTTPException` stay out of `crosscut`.
- **No single→multi-tenant plugin layer** in Phase 1. Demo multi-tenant claim handling
  (`tenant_roles`, active `tenant_id`) is explicit code, not an OCP framework.
- Prefer JWT as the production-shaped path; `api_key` / `none` / internal key remain
  for bootstrap and worker/service calls.

## Consequences

- Auth module size reflects multi-mode + claim normalization, not FastAPI Depends
  absence.
- Phase 2 hard tenancy can replace resolution/storage without rewriting routers that
  already take `AuthContext`.
- Contributors must not reintroduce Starlette/Dishka imports under `crosscut/auth`.
