# Eval harness (`tests/eval`)

Two live suites in one package, plus offline unittest. Live corpus is the synthetic investigation dossiers in [`resources/eval/`](../../resources/eval/).

`src/agentic_eval/core` is a **light shared settings abstraction** (OpenAI-compatible LiteLLM key + tenant) plus HTTP wrappers over generated OpenAPI clients. Custom DeepEval `BaseMetric` extensions live in `core/deepeval/`. Custom pydantic-evals `Evaluator` extensions live in `core/pydantic_evals/`. The `evaluate()` wrappers (display) live next to them. Each live suite has its own `settings.py` next to the runner. Typed goldens live in `core/golden/` (`GoldenDataset.load`). Live `evaluate()` / pydantic-evals live in `tests/generation` and `tests/retrieval`.

Live runs are **not** CI ([ADR 007](../../docs/adr/007-no-live-tests-in-ci.md)). Reports are **native SDK output** — DeepEval markdown under [`reports/eval/`](../../reports/eval/), pydantic-evals `report.print()` on stdout. There is no custom markdown writer and no `EVAL_PROFILE`.

## Quick start

```bash
# Offline — no stack, no judge LLM (~seconds)
make -C tests/eval run

# Live — needs `make up`, indexed dossiers, tests/eval/.env
cp tests/eval/.env.example tests/eval/.env   # add LiteLLM key

make -C tests/eval run-retrieval-suite    # retrieval IR (pydantic-evals print)
make -C tests/eval run-generation-suite   # DeepEval judge (slow; writes reports/eval/*.md)
make up-rerank                            # LiteLLM `rerank` → local TEI (precision)
```

---

## Suites

| Suite | Entry | Metrics | Report |
|-------|-------|---------|--------|
| **Retrieval** | `tests/retrieval/main.py` | Hit@k, **document** Recall@k, **chunk** Precision@k, MRR, nDCG@k | stdout (`report.print()`) |
| **Generation** | `tests/generation/main.py` | GEval Correctness, Faithfulness, Answer Relevancy, Required Phrases, Abstention | DeepEval `*_YYYYMMDD_HHMMSS.md` under `reports/eval/` |

Shared config: pydantic-settings. `CoreSettings` (OpenAI-compatible key, tenant, published api/chat URLs, `EVAL_*`). Suite gates in per-suite `settings.py`. Host process talks to **published compose ports**, not docker DNS.

Offline unittest still loads [`dataset.json`](dataset.json) (demo PDFs in [`resources/`](../../resources/)). Live gates use [`dataset-investigation.json`](dataset-investigation.json).

---

## Test cases (investigation)

Committed in [`dataset-investigation.json`](dataset-investigation.json).

### Retrieval (9 labeled questions)

Hits **`POST /v1/retrieval/search`** on the running api (`Product` over `ApiHttp`). The system must **find the right document** in the top‑k chunks before any LLM answer is judged. Scoring is a pydantic-evals `Dataset` + our `RetrievalIR` evaluator (`core/pydantic_evals/`).

| Tag | Example question | What we check |
|-----|------------------|---------------|
| **cross-doc** | *Which shell company appears in both dossiers, and what is its company registration number?* | Alpha + Beta linked facts (F‑01…F‑03) |
| **pii** | *What is Esther Szabo's tax identification number…?* | Alpha chunk with tokenized PII |
| **pii** | *What IBAN appears in the financial trace export…?* | Beta banking field |
| **F-05 / F-07** | *What aggregate HUF amount…?* / *What KAH case reference…?* | Single-doc facts |
| **decoy-trap** | *Is Kamuhold Építő Kft. the shell in ART-2024/8812? If not, which entity and registration?* | Must not confuse Gamma decoy with Alpha/Beta |
| **gamma-only** | *What penalty amount was assessed against Kamuhold Építő Kft. in 2023, and under which case reference?* | Answer only from Gamma decoy dossier |

### Generation (9 labeled + 3 abstention)

Talks to the running stack through **`ChatHttp` / `ApiHttp`** (`src/agentic_eval/core/clients/`), which compose the generated OpenAPI packages (`make generate-openapi-clients`). The generator returns the stream as a string; `ChatHttp.stream()` splits `event:` / `data:` frames. The generation `Product` only orchestrates eval (ephemeral session, catalog gate, vault-mark strip for the judge). `make -C tests/eval sync` generates the clients if they are missing.

**Labeled** — expect a concrete answer grounded in retrieved chunks:

- Cross-doc synthesis (shell company, Kamubank account, auditor witness)
- PII fields (tax ID, IBAN)
- Decoy disambiguation (Építő vs Beruházási Zrt.)
- Gamma-only penalty question

**Abstention** — expect a refusal (*“cannot find”*, *“not available”*, etc.):

| Question | Why abstain |
|----------|-------------|
| *What criminal classification applies to the HUF 47 million Kamuhold environmental matter?* | Gamma is administrative, not criminal — no answer in corpus |
| *Did Esther Szabo appear in the KAH-KV-2023/4419 environmental inspection?* | Name appears in Alpha/Beta only; environmental case is Gamma |
| *What mixture-of-experts routing algorithm…?* | Nonsense / out-of-corpus |

Abstention goldens go through a second `evaluate()` with `AbstentionMetric` only — they are not mixed into Faithfulness. Security-copy blocks are scored inside `AbstentionMetric` (`guard_block`), not as a labeled-case pre-filter.

---

## Metrics (plain language)

Each metric answers one question a non-technical reviewer would ask.

### Retrieval — “Did we open the right files?”

Imagine a clerk searching a filing cabinet and pulling **5 folders** (k=5). These are **IR metrics**, not DeepEval ContextualPrecision/Recall.

| Metric | Plain question | Life-like example | Gate |
|--------|----------------|-------------------|------|
| **Hit Rate@5** | Is **any** relevant dossier in the top 5? | Cross-doc question; Alpha is #2 → **hit = 1**. | ≥ 0.90 |
| **Document Recall@5** | What **fraction of the relevant set** did we find? | Relevant folders are Alpha **and** Beta. Top 5 is only Alpha → recall **0.5**, not 1.0. | ≥ 0.90 |
| **Chunk Precision@5** | How many of the 5 pulled **chunks** belong to the relevant set? | Relevant = {Alpha, Beta}; 3 Alpha + 1 Beta + 1 Gamma decoy → **0.80**. | ≥ 0.85 |
| **MRR** | How **high** is the first relevant folder? | First hit at #1 → 1.0; at #2 → 0.5. | ≥ 0.80 |
| **nDCG@5** | Are relevant folders **ranked near the top**, with credit for order? | Alpha, Beta, decoy… → high; decoy first → low. | ≥ 0.80 |

**Example:** *“Who is the auditor witness in both materials?”*
Relevant set is **Alpha and Beta**. Hit Rate passes if either appears. Document recall is 1.0 only if **both** appear in the top 5. Chunk precision drops when Gamma decoy or duplicate uploads fill slots.

Cross-doc goldens list `expected_source_files` (not a single file). Shared facts that appear in both Alpha and Beta (tax ID, ART-2024/8812, HUF 47.2M) also label both dossiers. Gamma stays off those sets — mentions there are decoy contrast, not answers. IBAN is Beta-only.

### Generation — “Is the answer true and on-topic?”

DeepEval uses a **judge LLM** (not the chat model) plus two deterministic `BaseMetric`s. **Correctness** compares the answer to the golden `expected_output`. Faithfulness only checks the retrieved chunks.

| Metric | Plain question | Life-like example | Gate |
|--------|----------------|-------------------|------|
| **Correctness (G-Eval)** | Does the answer contain the **key facts** from the expected output? | Expected: *Kamuhold Beruházási Zrt. (99-99-884422)*. Answer names that company and registration → pass, even if wording differs. | ≥ 0.80 |
| **Required phrases** | Does the answer **literally contain** annotated identifiers? | Must include the full IBAN, not a `HU68` prefix. Deterministic — no judge. | 100% of labeled |
| **Faithfulness** | Is the answer **supported by the retrieved excerpts** (no invented facts)? | Chunks say *HUF 47.2M*; answer says *47.2 million* → pass. Answer adds a person not in chunks → fail. | ≥ 0.85 |
| **Answer Relevancy** | Does the answer **address the question** without fluff? | Q: *Which account?* A: *99990001-00000001* → should pass (judge can be noisy). | ≥ 0.70 |
| **Abstention** | Labeled questions must **not** refuse; abstention goldens **must**. | Tax-ID answered; criminal-class Gamma question refused. | DeepEval `AbstentionMetric` |

Chat/API BanSubstrings rejects live in [`tests/api/features/05_guardrails.feature`](../api/features/05_guardrails.feature), not this package.

---

## Commands

| Make target (`tests/eval`) | Output |
|----------------------------|--------|
| `sync` | OpenAPI clients if missing, then `uv sync` |
| `unittest` | pytest unittest only |
| `run` | alias for `unittest` |
| `run-retrieval-suite` | pydantic-evals print |
| `run-generation-suite` | DeepEval markdown under `reports/eval/` |

DeepEval writes timestamped files (`investigation-generation_YYYYMMDD_HHMMSS.md`, `investigation-abstention_*.md`). The runner does **not** copy them to a stable filename — promote the latest into `reports/eval/investigation-generation.md` / `investigation-abstention.md` after a measured run.

### Latest measured run (2026-08-31)

Live stack (`make up` + rerank + guardrails), tenant `tenant-a`, k=5, 9 labeled + 3 abstention.

| Gate | Score | Threshold | Result |
|------|------:|----------:|--------|
| Hit Rate@5 | 1.00 | ≥ 0.90 | pass |
| Document Recall@5 | 0.89 | ≥ 0.90 | miss (cases 05, 08) |
| Chunk Precision@5 | 0.76 | ≥ 0.85 | miss (cases 05, 08) |
| MRR | 0.94 | ≥ 0.80 | pass |
| nDCG@5 | 0.93 | ≥ 0.80 | pass |
| Correctness (G-Eval) | 0.83 | ≥ 0.80 | pass (9/9) |
| Faithfulness | 1.00 | ≥ 0.85 | pass (9/9) |
| Answer Relevancy | 1.00 | ≥ 0.70 | pass (9/9) |
| Required phrases | 9/9 | 100% | pass |
| Abstention | 3/3 | 100% | pass |

Weak retrieval cases: **05** (KAH ART-2024/8812 — Beta missing from top-5) and **08** (Gamma decoy Építő vs Alpha/Beta Beruházási). Gates are tight on n=9. Full tables: [`reports/eval/`](../../reports/eval/).

---

## Layout

```
tests/eval/
├── README.md
├── dataset.json                 ← demo-PDF goldens (offline unittest)
├── dataset-investigation.json   ← live investigation goldens
├── .env.example                 ← copy to .env (gitignored)
├── src/agentic_eval/
│   ├── core/                    ← CoreSettings + clients/ (ChatHttp, ApiHttp)
│   │   ├── deepeval/            ← BaseMetric extensions + evaluate() wrapper
│   │   ├── pydantic_evals/      ← RetrievalIR Evaluator + evaluate() wrapper
│   │   └── golden/              ← Golden / LabeledGolden / AbstentionGolden + GoldenDataset
└── tests/
    ├── unittest/                ← offline (CI-safe); pytest testpaths
    ├── retrieval/               ← live pydantic-evals (`main.py`) + Product + settings.py
    └── generation/              ← live DeepEval (`main.py`) + Product + settings.py
```

---

## Prerequisites (live)

1. Stack up: `make up` (+ `make up-rerank` for LiteLLM rerank; `make up-guardrails` if chat should scan prompts).
2. Vault + index flags in repo `.env` (`PII_VAULT_ENABLED`, `INDEXING_PDF_PII_TOKENIZATION_ENABLED`).
3. Index three dossiers under `EVAL_TENANT_ID` (see [`resources/eval/README.md`](../../resources/eval/README.md)).
4. `tests/eval/.env`: LiteLLM key, `EVAL_SUT_CHAT_URL` / `EVAL_SUT_API_URL`, and `INTERNAL_SERVICE_KEY` when `AUTH_MODE=jwt`.

Upload uses `X-Internal-Service-Key` when `AUTH_MODE=jwt`.
