# Ops operator

Host entrypoint is **Docker Compose**, not Make. The image runs **`make initialization`** (infra) then **`make bootstrap`** (after apps are up), then stays idle so operator commands run **inside** the container.

The image does not call Docker. Stack up/down is Compose on the host.

## Host (Docker only)

Default lab (app [`http://localhost:5173`](http://localhost:5173), Keycloak [`http://localhost:8080`](http://localhost:8080), APIs `:8000` / `:8002` / `:8003`). Login **`admin` / `admin`**.

```bash
docker compose up -d
```

Tests (QA image, host network so demo ports work):

```bash
docker compose --profile qa run --rm qa                 # system-test, then stop
docker compose --profile qa run --rm qa make unittest
```

Traefik ingress (only `:80`; set `KC_HOSTNAME_PORT=80` and `VITE_KEYCLOAK_URL=http://localhost`):

```bash
AUTH_MODE=jwt VITE_AUTH_ENABLED=true \
  docker compose --profile auth \
  -f docker-compose.yml -f operations/compose.ingress.yaml up -d --build
```

Optional sidecars:

```bash
docker compose --profile guardrails up -d
```

Stop / erase:

```bash
docker compose down      # stop containers, keep data volumes
docker compose down -v   # erase: containers + volumes (Postgres, MinIO, Qdrant, …)
```

## Commands in the ops container

After the stack is up (ops is healthy). Recipes: `tools/ops/Makefile`.

```bash
docker compose exec ops make initialization  # infra: MinIO bucket + CORS, demo PDFs
docker compose exec ops make bootstrap    # after apps: migrate, users, reindex
docker compose exec ops make teardown     # wipe Postgres / MinIO / Qdrant / Redis
docker compose exec ops make restart      # teardown, start, bootstrap
docker compose exec ops make resources    # demo PDFs → resources/
docker compose exec ops make add-users    # Keycloak demo/test personas (auth profile)
docker compose exec ops make add-user USERNAME=dev@local PASSWORD=dev TENANT=tenant-a ORGS=tenant-a ROLES=tenant-a=read+write
docker compose exec ops make index        # reindex via api
```

`initialization` is infrastructure only (`setup-minio` + `DEMO_RESOURCES`). `bootstrap` waits for the api, then Alembic migrate, Keycloak users (`DEMO_USERS`; skipped if Keycloak is down), and reindex. `teardown` clears app data only (not the Keycloak database).

`add-users` seeds the same personas live tests use (`admin`, `alice@tenant-a.local`, `bob@tenant-b.local`, `writer@tenant-a.local`, `reader@tenant-a.local`). Catalog: `DEMO_USERS` in `tools/ops/Makefile`. Tests run in the **qa** image (`docker compose --profile qa run --rm qa make unittest|system-test`), not in ops.

## Layout

| Path | Role |
|------|------|
| `Dockerfile` | `make initialization` then `make bootstrap`, then idle |
| `Makefile` | `initialization` (infra) / `bootstrap` (after apps) / `teardown` / `restart` |
