# Presidio analyzer (PII detect)

Compose profile: **`guardrails`**. Internal DNS: `presidio-analyzer:3000`.

```bash
make up-guardrails
```

Used by shared `AnalyzerClient` (`ANALYZER_API_BASE`) and optionally by LiteLLM's built-in `presidio-pii` guardrail.
