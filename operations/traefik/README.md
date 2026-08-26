# Traefik

API gateway — **JWT auth** for `/api` and `/chat` when using `--profile auth`.

- Entrypoint: `:80` (override with `TRAEFIK_HTTP_PORT`)
- Dashboard (insecure): `:8088`

## Auth flow

1. Client obtains Bearer token from Keycloak (`tenant_id` claim in access token).
2. Traefik `keycloak-jwt` middleware validates JWT via Keycloak JWKS.
3. Valid requests are forwarded with headers:
   - `X-Tenant-Id` ← `tenant_id` claim
   - `X-User-Id` ← `sub`

Public routes (no JWT): `/`, `/realms/*`, `/resources/*` (Keycloak OIDC). App admin UI: `/admin` (React SPA).

```bash
docker compose --profile auth --profile ui up -d
# API via gateway:
curl -H "Authorization: Bearer $TOKEN" http://localhost/api/v1/documents
```
