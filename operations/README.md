# Operations / platform services

Docker Compose **include** fragments — one folder per dependency.

| Path | Service | Port |
|------|---------|------|
| `postgres/` | PostgreSQL 16 | 5432 |
| `redis/` | Redis 7 | 6379 |
| `minio/` | MinIO | 9000 / 9001 |
| `qdrant/` | Qdrant | 6333 |
| `litellm/` | LiteLLM proxy | 4000 |
| `llm-guard/` | PromptInjection DeBERTa (`--profile guardrails`) | internal |
| `presidio-analyzer/` | PII detect (default stack) | 5002 |
| `presidio-anonymizer/` | PII redact (default stack) | 5001 |
| `rerank/` | TEI MiniLM reranker (default demo) | 8090 |
| `keycloak/` | Keycloak + org bootstrap (default demo) | 8080 |
| `traefik/` | API gateway (`--profile auth`) | 80 |

App Dockerfiles live under each project: `services/*/Dockerfile`, `frontend/app-ui/Dockerfile`, `frontend/admin-app-ui/Dockerfile`.

Post-start **`make initialization`** then **`make bootstrap`** (infra, then migrate/users/reindex after apps): **`tools/ops`**.

## Postgres init

`postgres/init/` creates:

- `agentic_rag_eval` — via `POSTGRES_DB` env
- `keycloak` — via `01-create-databases.sql`

## Usage

Host commands are Docker Compose — not Make. Full recipes: [`tools/ops/README.md`](../tools/ops/README.md).

```bash
docker compose up -d --build
docker compose --profile guardrails up -d
AUTH_MODE=jwt VITE_AUTH_ENABLED=true \
  docker compose --profile auth \
  -f docker-compose.yml -f operations/compose.ingress.yaml up -d --build
docker compose exec ops make add-users
docker compose down
```
