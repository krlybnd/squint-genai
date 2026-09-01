# Keycloak Admin REST API — OpenAPI (official)

Vendor copy of the **Keycloak Admin REST API** OpenAPI 3.0 definitions published by the Keycloak project (preview feature in upstream docs).

| File | Format |
|------|--------|
| `admin-rest.openapi.yaml` | YAML (preferred for diff/review) |
| `admin-rest.openapi.json` | JSON |

## Source (refresh)

Download the current official artifacts from:

- YAML: https://www.keycloak.org/docs-api/latest/rest-api/openapi.yaml
- JSON: https://www.keycloak.org/docs-api/latest/rest-api/openapi.json
- Human-readable reference: https://www.keycloak.org/docs-api/latest/rest-api/

```bash
curl -fsSL -o admin-rest.openapi.yaml \
  https://www.keycloak.org/docs-api/latest/rest-api/openapi.yaml
curl -fsSL -o admin-rest.openapi.json \
  https://www.keycloak.org/docs-api/latest/rest-api/openapi.json
```

Regenerate the **async httpx** Python workspace client (gitignored under `packages/generated/`):

```bash
make generate-openapi-clients
uv sync --all-packages
```

Import: `keycloak_admin_client` — use `AuthenticatedClient` + endpoint `asyncio` / `asyncio_detailed` helpers.

## Version note

Docker Compose pins Keycloak **`26.0.7`** (`operations/keycloak/compose.yaml`). Keycloak does not publish a version-pinned OpenAPI URL for every patch release; this directory tracks **`docs-api/latest`** from keycloak.org. Regenerate after upgrading the Keycloak image if admin API paths or schemas changed.

## Usage in this repo

Reference for scripts such as `scripts/keycloak/init-organizations.sh` (Organizations admin endpoints under `/admin/realms/{realm}/organizations`).
