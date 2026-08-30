# LiteLLM

OpenAI-compatible LLM and embedding proxy (rerank alias kept for legacy `.env` only — apps no longer call it).

- Port: `:4000`
- Config: `litellm.config.yaml`
- Apps call **role aliases** (`generate`, `router`, `judge`, `embed`), not provider model ids.

| Alias | Backend (default) | Used by |
|-------|-------------------|---------|
| `router` | `gpt-4o-mini` | Query rewrite, session titles |
| `generate` | `gpt-4o-mini` | RAG answers, comment moderation |
| `judge` | `gpt-4o` | DeepEval generation gate (no fallback to `generate`) |
| `embed` | `text-embedding-3-small` | Indexing + query embeddings |
| `rerank` | Cohere `rerank-multilingual-v3.0` | Optional retrieval rerank |
| `generate-guarded` | same as `generate` + `local-cpu-guards` | Opt-in guarded chat (#29) |
| `router-guarded` | same as `router` + `local-cpu-guards` | Opt-in guarded rewrite |

Legacy names (`gpt-4o-mini`, `text-embedding-3-small`, `rerank-multilingual-v3.0`) remain registered so existing `.env` values keep working.

### Guardrails (optional)

Requires `make up-guardrails` (compose profile `guardrails` → `llm-guard` + `presidio-analyzer` + `presidio-anonymizer`).

| Guardrail alias | Backend |
|-----------------|---------|
| `local-cpu-guards` | Presidio MASK + llm-guard PromptInjection (used by `*-guarded`) |
| `presidio-pii` | Presidio only (request-body experiments) |
| `prompt-injection` | llm-guard only (request-body experiments) |

Unguarded aliases stay the app default so eval/`judge`/`embed` are unaffected.

All Python services call LiteLLM — never OpenAI or Cohere directly. Recreate the `litellm` container after changing this config (`docker compose up -d litellm`).
