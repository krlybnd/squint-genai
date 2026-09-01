# Keycloak

Identity provider with **Organizations multitenancy**. Starts with the default Compose demo (`docker compose up -d`). Traefik remains `--profile auth`.

Requires Postgres database `keycloak` (see `operations/postgres/init/`).

## Realm export

`realm/agentic-rag-eval-realm.json` — imported on startup (this file only; `user-profile.json` stays out of the import dir so Keycloak 26 does not treat it as a realm).

Official **Admin REST OpenAPI** (vendor copy): `openapi/admin-rest.openapi.yaml`. See `openapi/README.md` for the download URL, refresh steps, and **`make generate-openapi-clients`** (async httpx Python client in `packages/generated/`, gitignored).

| Setting | Value |
|---------|--------|
| Organizations | enabled (`KC_FEATURES=organization`) |
| Claim in bearer token | `tenant_id` (protocol mapper on client scope `tenant`) |
| Demo users | **`admin` / `admin`** (full access), `alice@tenant-a.local` / `alice`, `bob@tenant-b.local` / `bob`, `writer@tenant-a.local` / `writer`, `reader@tenant-a.local` / `reader` |

Organizations (`tenant-a`, `tenant-b`) are created by `keycloak-init` after import (orgs cannot be defined in realm.json).

`keycloak-init` also applies the declarative **user profile** from `realm/user-profile.json` so `tenant_id` and `tenant_roles` user attributes persist (Keycloak 26 drops undeclared attributes). Demo and live-test personas are seeded via `make add-users` (`DEMO_USERS` in `tools/ops/Makefile`).

To re-apply profile + seed users without resetting the DB:

```bash
docker compose run --rm keycloak-init
# or, with the stack already up:
docker compose exec ops make add-users
```

## User profile (multitenancy attributes)

Keycloak 26+ uses a declarative user profile. Custom attributes must be declared or they are silently dropped on write.

| Attribute | Purpose |
|-----------|---------|
| `tenant_id` | Active tenant alias (JWT `tenant_id` claim via protocol mapper) |
| `tenant_roles` | JSON map of tenant alias → role list (`read` / `write` / `admin`) |

Configuration lives in `realm/user-profile.json` and is applied on every `keycloak-init` run via `PUT /admin/realms/{realm}/users/profile`. Fresh imports also get it from the realm `components` block.

If demo user email/names are still empty after a bad partial update, reset the Keycloak DB (below) or re-run `keycloak-init` / `make add-users`.

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

The **admin** service (`services/admin`, port 8003, Traefik `/admin-api`) manages Organizations (tenants) and users via the generated `keycloak-admin-client`. It authenticates with **client credentials** using confidential client `agentic-rag-eval-admin` (read **and** write: `manage-realm`).

The **api** service uses a **separate secret** (`agentic-rag-eval-api`) for tenancy read (`GET /v1/me`) and a narrow write (`PUT /v1/me/active-tenant` → user attributes). That service account has `view-users`, `view-realm`, and `manage-users`. It does **not** have `manage-realm`. Chat and indexing do not receive either client secret.

Keycloak 26 Organizations `GET /organizations` requires `manage-realm` (there is no `view-organizations` role). The api therefore must **not** list the org catalog. Membership for `GET /v1/me` uses `GET /organizations/members/{id}/organizations` (allowed with `view-users`) plus user attributes. Admin keeps `manage-realm` so it can list/create orgs.

The realm export grants:

| Service account | Capability | realm-management roles |
|-----------------|------------|------------------------|
| `service-account-agentic-rag-eval-api` | read membership + write active tenant | `manage-users`, `view-users`, `view-realm` |
| `service-account-agentic-rag-eval-admin` | org/user CRUD | `manage-users`, `view-users`, `manage-realm`, `view-realm` |

Compose (not a shared `x-app-env` secret):

- api: `KEYCLOAK_ADMIN_CLIENT_ID=agentic-rag-eval-api` / `KEYCLOAK_API_CLIENT_SECRET`
- admin: `KEYCLOAK_ADMIN_CLIENT_ID=agentic-rag-eval-admin` / `KEYCLOAK_ADMIN_S2S_CLIENT_SECRET`

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
docker compose up -d keycloak keycloak-init
```
