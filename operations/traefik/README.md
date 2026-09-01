# Traefik

API gateway — **JWT auth** for `/api` and `/chat` when using `--profile auth`.

- Entrypoint: `:80` (override with `TRAEFIK_HTTP_PORT`)
- Dashboard is not published (auth demo uses `compose.ingress.yaml`)

## Auth flow

1. Client obtains Bearer token from Keycloak (`tenant_id` claim in access token).
2. Traefik `keycloak-jwt` middleware validates JWT via Keycloak JWKS.
   - Traefik waits for Keycloak **healthy** before starting (see `compose.yaml`).
   - `ForceRefreshKeys` refetches JWKS when a token references an unknown `kid`.
   - If API calls return **403** with body `token validation failed`, restart Traefik after Keycloak is up: `docker compose restart traefik`.
3. Valid requests are forwarded with headers:
   - `X-Tenant-Id` ← `tenant_id` claim
   - `X-User-Id` ← `sub`

Public routes (no JWT): `/`, `/realms/*`, `/resources/*` (Keycloak OIDC), `/api/health`, `/chat/health`, `/admin-api/health`. App admin UI: `/admin` (React SPA). Guardrails host-port stand-ins when `compose.ingress.yaml` unpublishes `:8010` / `:5002`: `/guard` → llm-guard, `/analyzer` → Presidio analyzer (own Bearer token, not Keycloak JWT).

```bash
# Auth overlay — tools/ops/README.md
curl -H "Authorization: Bearer $TOKEN" http://localhost/api/v1/documents
```
