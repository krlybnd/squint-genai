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

Legacy names (`gpt-4o-mini`, `text-embedding-3-small`, `rerank-multilingual-v3.0`) remain registered so existing `.env` values keep working.

### Guardrails

Chat/api call **llm-guard + Presidio HTTP clients** directly (`make up-guardrails`). The proxy keeps an optional built-in `presidio-pii` guardrail for request-body experiments only — no custom Python guardrail plugins.

All Python services call LiteLLM — never OpenAI or Cohere directly. Recreate the `litellm` container after changing this config (`docker compose up -d litellm`).
