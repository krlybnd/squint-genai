# Keycloak

Identity provider with **Organizations multitenancy** (`--profile auth`).

Requires Postgres database `keycloak` (see `operations/postgres/init/`).

## Realm export

`realm/agentic-rag-eval-realm.json` — imported on startup.

Official **Admin REST OpenAPI** (vendor copy): `openapi/admin-rest.openapi.yaml` (+ `.json`). See `openapi/README.md` for download URLs, refresh steps, and **`make generate-keycloak-client`** (async httpx Python client in `packages/generated/`, gitignored).

| Setting | Value |
|---------|--------|
| Organizations | enabled (`KC_FEATURES=organization`) |
| Claim in bearer token | `tenant_id` (protocol mapper on client scope `tenant`) |
| Demo users | **`admin` / `admin`** (full access), `alice@tenant-a.local` / `alice`, `bob@tenant-b.local` / `bob` |

Organizations (`tenant-a`, `tenant-b`) are created by `keycloak-init` after import (orgs cannot be defined in realm.json).

## Token claims

Access token includes:

```json
{
  "tenant_id": "tenant-a",
  "sub": "..."
}
```

Obtain token (password grant — dev only):

```bash
curl -s -X POST "http://localhost/realms/agentic-rag-eval/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=agentic-rag-eval-dev" \
  -d "username=alice@tenant-a.local" \
  -d "password=alice" \
  -d "scope=openid tenant" | jq -r .access_token
```

Decode at [jwt.io](https://jwt.io) to verify `tenant_id`.

## Admin API (Keycloak Admin REST)

The **admin** service (`services/admin`, port 8003, Traefik `/admin-api`) manages Organizations (tenants) and users via the generated `keycloak-admin-client`. It authenticates to Keycloak with **client credentials** using the existing confidential client `agentic-rag-eval-api` (not the master admin password).

The realm export grants that client’s service account user `service-account-agentic-rag-eval-api` these **realm-management** client roles: `manage-users`, `view-users`, `manage-realm`, `view-realm`.

Set in `.env` (see `.env.example`):

- `KEYCLOAK_ADMIN_CLIENT_ID=agentic-rag-eval-api`
- `KEYCLOAK_ADMIN_CLIENT_SECRET` — must match the client secret in the realm export

After editing `realm/agentic-rag-eval-realm.json` (including service-account roles), reset the Keycloak DB (below) so `--import-realm` runs again.

## Start

```bash
make up-auth
# App (OIDC login): http://localhost — realm user admin / admin
# Traefik :80 — JWT auth on /api and /chat
# Keycloak console: http://localhost/admin (master admin admin / admin)
```

After changing `realm/agentic-rag-eval-realm.json`, reset the Keycloak DB so `--import-realm` runs again:

```bash
docker compose exec postgres psql -U agentic -d postgres -c \
  "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'keycloak' AND pid <> pg_backend_pid(); \
   DROP DATABASE IF EXISTS keycloak; CREATE DATABASE keycloak; GRANT ALL PRIVILEGES ON DATABASE keycloak TO agentic;"
docker compose --profile auth up -d keycloak keycloak-init
```
