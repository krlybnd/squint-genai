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
| `presidio-analyzer/` | PII detect (`--profile guardrails`) | internal |
| `presidio-anonymizer/` | PII redact (`--profile guardrails`) | internal |
| `rerank/` | TEI MiniLM reranker (`--profile rerank`) | 8090 |
| `keycloak/` | Keycloak + org bootstrap (`--profile auth`) | via Traefik `/realms` |
| `traefik/` | API gateway + JWT auth (`--profile auth`) | 80 / 8088 |

App Dockerfiles live under each project: `services/*/Dockerfile`, `frontend/app-ui/Dockerfile`, `frontend/admin-app-ui/Dockerfile`.

Post-start bootstrap (Alembic migrate + MinIO bucket/CORS): **`tools/ops`** — Dagger module + lightweight `ops` compose service.

## Postgres init

`postgres/init/` creates:

- `agentic_rag_eval` — via `POSTGRES_DB` env
- `keycloak` — via `01-create-databases.sql`

## Usage

```bash
make up              # infra + app services + ops bootstrap
make up-guardrails   # optional: llm-guard + Presidio (profile guardrails) for chat/api Guard clients
make up-rerank       # optional: TEI reranker (profile rerank) for LiteLLM alias `rerank`
make up-auth         # + Traefik + Keycloak (profiles auth + ui)
docker compose --profile auth --profile ui up -d
make ops-bootstrap   # run bootstrap via Dagger (host env)
```
