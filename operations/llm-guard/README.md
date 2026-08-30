# llm-guard-api (BanSubstrings + PromptInjection / DeBERTa)

Compose profile: **`guardrails`** (with Presidio siblings). Internal DNS: `llm-guard:8000`.

```bash
make up-guardrails
```

Config: `config/scanners.yml` — **BanSubstrings** first (deterministic API-acceptance fixtures), then PromptInjection.

Chat/api call this service via shared `GuardClient` (`GUARD_API_BASE`), not via LiteLLM custom plugins.
Auth: Bearer `${LLM_GUARD_AUTH_TOKEN:-poc-local-classifier}`.

HF cache default: `pocs/local_classifier/run/hf-cache` (override `LLM_GUARD_HF_CACHE`).
~1.7 GiB RSS after first PromptInjection model load. Upstream image is archived — demo only.

Host port (acceptance tests): `:8010`.
