# LiteLLM

OpenAI-compatible LLM, embedding, and rerank proxy.

- Port: `:4000`
- Config: `litellm.config.yaml`
- Rerank (optional): `POST /rerank` — Cohere `rerank-multilingual-v3.0` via `COHERE_API_KEY`. OpenAI has no rerank API; keep `RERANK_ENABLED=false` unless Cohere is configured.

All Python services call LiteLLM — never OpenAI or Cohere directly.
