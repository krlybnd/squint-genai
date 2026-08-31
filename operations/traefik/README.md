# Traefik

API gateway — **JWT auth** for `/api` and `/chat` when using `--profile auth`.

- Entrypoint: `:80` (override with `TRAEFIK_HTTP_PORT`)
- Dashboard (insecure): `:8088` — **lab** (`make up-auth`) only; unpublished in `make up-demo`

## Auth flow

1. Client obtains Bearer token from Keycloak (`tenant_id` claim in access token).
2. Traefik `keycloak-jwt` middleware validates JWT via Keycloak JWKS.
   - Traefik waits for Keycloak **healthy** before starting (see `compose.yaml`).
   - `ForceRefreshKeys` refetches JWKS when a token references an unknown `kid`.
   - If API calls return **403** with body `token validation failed`, restart Traefik after Keycloak is up: `docker compose restart traefik`.
3. Valid requests are forwarded with headers:
   - `X-Tenant-Id` ← `tenant_id` claim
   - `X-User-Id` ← `sub`

Public routes (no JWT): `/`, `/realms/*`, `/resources/*` (Keycloak OIDC). App admin UI: `/admin` (React SPA).

```bash
# Lab (host ports published, including Traefik dashboard :8088):
make up-auth
# Demo (Traefik :80 only — see operations/compose.ingress.yaml):
make up-demo
# API via gateway:
curl -H "Authorization: Bearer $TOKEN" http://localhost/api/v1/documents
```
