# LiteLLM

OpenAI-compatible LLM, embedding, and rerank proxy.

- Port: `:4000`
- Config: `litellm.config.yaml`
- Apps call **role aliases** (`generate`, `router`, `judge`, `embed`, `rerank`), not provider model ids.
- Rerank (optional): `POST /rerank` — Cohere via the `rerank` alias (`COHERE_API_KEY`). OpenAI has no rerank API; keep `RERANK_ENABLED=false` unless Cohere is configured.

| Alias | Backend (default) | Used by |
|-------|-------------------|---------|
| `router` | `gpt-4o-mini` | Query rewrite, session titles |
| `generate` | `gpt-4o-mini` | RAG answers, comment moderation |
| `judge` | `gpt-4o` | DeepEval generation gate (no fallback to `generate`) |
| `embed` | `text-embedding-3-small` | Indexing + query embeddings |
| `rerank` | Cohere `rerank-multilingual-v3.0` | Optional retrieval rerank |

Legacy names (`gpt-4o-mini`, `text-embedding-3-small`, `rerank-multilingual-v3.0`) remain registered so existing `.env` values keep working.

All Python services call LiteLLM — never OpenAI or Cohere directly. Recreate the `litellm` container after changing this config (`docker compose up -d litellm`).
