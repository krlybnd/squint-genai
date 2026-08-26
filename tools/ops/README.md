# Ops bootstrap container

Post-start bootstrap for the agentic-rag-eval stack:

1. Wait for Postgres, MinIO, and app `/health` endpoints
2. **Alembic** `upgrade head`
3. **MinIO** — create `documents` bucket + CORS (presigned browser uploads)

Runs as a one-shot **`ops`** service in `docker compose up` after api, chat, and indexing have started.

## Image

Lightweight `python:3.12-alpine` + `bash`, `mc`, `curl`, `psql` — Python only for Alembic CLI.

Build via Docker Compose (repo root context):

```bash
docker compose build ops
```

Run bootstrap manually:

```bash
make ops-bootstrap   # docker compose run --rm ops
```

## Local migrate only

```bash
make db-migrate   # uses packages/shared venv (Alembic)
```
