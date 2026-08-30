# PoC: local_classifier

> ADR 010. Proof log: `results/result.log` (**gitignored**). Run `./scripts/poc.sh`.

## Hypothesis

Local CPU containers for **Presidio** (PII) + **llm-guard PromptInjection**
(ProtectAI DeBERTa) can run on a notebook and give demo-credible guardrail
signals without a GPU — at the cost of ~2+ GiB RSS and a model download under
`run/`.

## Questions we care about

- [x] Runs on notebook CPU (no GPU)?
- [x] Rough RSS / disk under `run/` acceptable for a demo?
- [x] Smoke proves happy path + fail path?
- [x] Upstream/licence OK for a short-lived demo?
- [ ] Can it sit behind LiteLLM / chat guard without breaking unrelated aliases?

## Success criteria

- Presidio detects email; anonymizer redacts it.
- llm-guard: benign `is_valid: true`; attack-ish `is_valid: false`.
- `poc.sh` exits 0 and leaves an informative `results/result.log`.

## Out of scope

- Wiring into root compose / LiteLLM (#29).
- Full llm-guard scanner suite.
- vLLM / generative local LLM.

## Harness

| Item | Value |
|------|--------|
| Path | `pocs/local_classifier/` |
| Entry | `./scripts/poc.sh` |
| Ports | llm-guard `:8010`, analyzer `:5002`, anonymizer `:5001` |
| Related | [#29](https://github.com/krlybnd/squint-genai/issues/29) |

## Proof (from `results/result.log`)

_Local run 2026-08-30 (full log in the PoC PR; `results/` stays gitignored):_

- compose up + all three health checks OK
- presidio analyze: EMAIL_ADDRESS; anonymize redacts email
- llm-guard benign `is_valid=true`; attack `is_valid=false`
- RSS: llm-guard **1.711 GiB**, analyzer **773.4 MiB**, anonymizer **51.38 MiB**; `run/` **716M** HF cache

## Interpretation

- CPU-only path works; DeBERTa dominates RSS on first analyze.
- llm-guard upstream is **archived** — OK for demo, weak long-term; useful reference for #29.
- LiteLLM wiring not exercised (question left open).

## Decision

- [x] **Ship** — productize (link issue)
- [ ] **Iterate** — change harness, re-run `poc.sh`
- [ ] **Abandon** — why

**Notes:** Proceed via [#29](https://github.com/krlybnd/squint-genai/issues/29). Do not commit `results/` or `run/`.
