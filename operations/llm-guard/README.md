# llm-guard-api (BanSubstrings + PromptInjection / DeBERTa)

Compose profile: **`guardrails`** (with Presidio siblings). Internal DNS: `llm-guard:8000`.

```bash
make up-guardrails
```

Config: `config/scanners.yml` — **BanSubstrings** first (deterministic demo/API bans: `motherfucker`, `fuck you`, `squint-e2e-banned`), then PromptInjection.

LiteLLM uses this via `local-cpu-guards` / `prompt-injection` (see `operations/litellm/`).
Auth: Bearer `${LLM_GUARD_AUTH_TOKEN:-poc-local-classifier}`.

HF cache default: `pocs/local_classifier/run/hf-cache` (override `LLM_GUARD_HF_CACHE`).
~1.7 GiB RSS after first PromptInjection model load. Upstream image is archived — demo only.

Host port (acceptance tests): typically `:8010` — see compose `ports` / root `.env`.
