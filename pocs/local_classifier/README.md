# Local classifier PoC (CPU) — ADR 010

Standalone **Presidio** (PII) + **llm-guard-api** (prompt-injection / DeBERTa).
Not wired into the main Squint compose or LiteLLM yet.

See **[poc.md](./poc.md)** for hypothesis, questions, and decision.
Proof: `./scripts/poc.sh` → `results/result.log` (**gitignored**).

## Quick start

```bash
cd pocs/local_classifier
docker compose up -d
./scripts/poc.sh
```

Stop: `docker compose down`

## Ports

| Service | Host | Notes |
|---------|------|--------|
| llm-guard-api | `localhost:8010` | `GET /healthz`, `POST /analyze/prompt` |
| presidio-analyzer | `localhost:5002` | PII detect |
| presidio-anonymizer | `localhost:5001` | PII redact |

Auth for llm-guard: Bearer `poc-local-classifier`.

## Notes

- llm-guard upstream is **archived** — PoC/demo only.
- Product path: GitHub #29. Workflow: ADR 010 + `.cursor/skills/poc`.
