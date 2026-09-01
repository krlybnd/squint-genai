# PostgreSQL

Shared Postgres instance for **agentic-rag-eval** and **Keycloak**.

| Database | Owner | Purpose |
|----------|-------|---------|
| `agentic_rag_eval` | `agentic` | App (sessions, documents, jobs) |
| `keycloak` | `agentic` | Keycloak (default demo) |

Init scripts in `init/` run on first container start only.

```bash
# Connect locally
psql postgresql://agentic:agentic@localhost:5432/agentic_rag_eval
```
