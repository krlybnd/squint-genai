# Text Embeddings Inference (rerank)

Starts with the default Compose demo (`docker compose up -d`). Internal DNS: `tei-rerank:80`. Host port: `:8090`.

Model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (CPU image `cpu-1.8`).

LiteLLM alias `rerank` (and legacy `rerank-multilingual-v3.0`) forwards Cohere-style `/rerank` to this service. Chat/api/eval call the proxy, not TEI directly.

HF cache default: `pocs/local_classifier/run/hf-cache` (override `LLM_GUARD_HF_CACHE`). First start downloads the MiniLM weights.

If TEI is down, retrieval fail-opens to hybrid RRF.
