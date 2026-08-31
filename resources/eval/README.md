# Eval golden corpus — synthetic investigation dossiers

**Status:** committed Markdown source; convert to PDF/DOCX locally for indexing.

> **WARNING — TEST MATERIAL ONLY**
> All persons, companies (Kamu* prefix), banks, IBANs, tax IDs, case numbers, and addresses in this folder are **entirely fictional**.
> **No real company, account number, or IBAN appears** — names follow eval conventions (`Kamuhold`, `Kamubank`, `KamuBridge`, `KAH`).
> Generated for Squint RAG / PII vault / guardrails / DeepEval testing. **Do not treat as real legal records.**

## Files

| File | Role | Pages (target) |
|------|------|----------------|
| [investigation-dossier-alpha.md](investigation-dossier-alpha.md) | Primary procurement-fraud investigation | ~10 |
| [investigation-dossier-beta.md](investigation-dossier-beta.md) | Financial trace — **genuinely linked** to Alpha | ~10 |
| [investigation-dossier-gamma-decoy.md](investigation-dossier-gamma-decoy.md) | Environmental penalty — **decoy** (similar names, different case) | ~10 |

## Convert to PDF (optional)

```bash
# requires pandoc + a PDF engine (texlive, wkhtmltopdf, etc.)
pandoc resources/eval/investigation-dossier-alpha.md -o resources/eval/investigation-dossier-alpha.pdf
pandoc resources/eval/investigation-dossier-beta.md  -o resources/eval/investigation-dossier-beta.pdf
pandoc resources/eval/investigation-dossier-gamma-decoy.md -o resources/eval/investigation-dossier-gamma-decoy.pdf
```

Index with vault flags enabled (`INDEXING_PDF_PII_TOKENIZATION_ENABLED=true`, `PII_VAULT_ENABLED=true`).

## Cross-document ground truth (Alpha + Beta only)

| ID | Finding | Alpha | Beta |
|----|---------|-------|------|
| F-01 | Shell company | Kamuhold Beruházási Zrt. (reg. 99-99-884422) | Same entity, ownership chain |
| F-02 | Intermediary account | Kamubank 99990001-00000001 | Same account, transfer 2024-04-12 |
| F-03 | Auditor witness | Dr. Levente Varga | Deposition transcript |
| F-04 | Time window | Q2 2024 | April–June 2024 |
| F-05 | Aggregate amount | HUF 47.2M hidden commission | HUF 47.2M consolidated trace |
| F-06 | Natural person | Esther Szabo (tax ID 99999999-9-99) | Same tax ID on delegation / outbound trace |
| F-07 | Tax authority flag | KAH referral ART-2024/8812 | Cross-reference to Alpha |

**Gamma decoy traps:** Kamuhold **Építő** Kft. (not Beruházási Zrt.), HUF **47M** environmental fine (2023), case KAH-KV-2023/4419 — **not** criminal procurement.

## Eval rubric (recommended gates)

| Tier | Metric | Threshold | Notes |
|------|--------|-----------|-------|
| S0 | Plaintext PII in indexed chunks | **0 hits** | API `06_pii_vault` + regex |
| S0 | Vault token present after index | **100%** | Known entities from dossiers |
| S0 | Cross-tenant detokenize leak | **0%** | Tenant isolation |
| S1 | Guardrails BanSubstrings | **100%** | `05_guardrails` |
| R1 | Hit Rate@5 | **≥ 0.90** | Any relevant dossier in top 5 |
| R1 | Document Recall@5 | **≥ 0.90** | Fraction of the **relevant set** found (cross-doc = Alpha **and** Beta) |
| R1 | Chunk Precision@5 | **≥ 0.85** | Chunks from the relevant set; Gamma decoy is not relevant for Alpha/Beta questions |
| G2 | Correctness (G-Eval) | **≥ 0.80** | Answer contains key facts from `expected_output` |
| G2 | Required phrases | **100%** | Deterministic IDs / names in the answer |
| G2 | Faithfulness (DeepEval) | **≥ 0.85** | Groundedness vs retrieved chunks (not vs gold) |
| G2 | Answer Relevancy | **≥ 0.70** | On-topic vs the question |
| A0 | Abstention (Gamma-only criminal Q) | **100%** | Must refuse or deny criminal link |

## Golden datasets (committed)

| File | Purpose |
|------|---------|
| [`tests/eval/dataset-investigation.json`](../../tests/eval/dataset-investigation.json) | Retrieval / generation / abstention goldens |

Use `.md` source filenames in goldens until PDF conversion. Run offline checks: `make -C tests/eval run`.

**Eval harness docs (cases, metrics, examples):** [`tests/eval/README.md`](../../tests/eval/README.md).

### Live eval (LLM judge)

Index the three dossiers first (PDF or MD upload, vault ON recommended). Then:

```bash
cp tests/eval/.env.example tests/eval/.env   # LiteLLM key

# Tier R1 — retrieval IR (no judge LLM; pydantic-evals print)
make eval-live

# Tier G2 — DeepEval (native timestamped markdown under reports/eval/)
make eval-live-generation
```

Generation writes DeepEval's own markdown under [`reports/eval/`](../../reports/eval/). Retrieval prints to stdout.

BanSubstrings / chat guard rejects: [`tests/api/features/05_guardrails.feature`](../../tests/api/features/05_guardrails.feature) (`make test-api`, needs `make up-guardrails`).

Replace `.pdf` with `.md` until converted, or index PDFs after pandoc.

## Embedded PII (all fictional — for vault tests)

| Field | Value | Dossier |
|-------|-------|---------|
| Name | Esther Szabo | Alpha, Beta |
| Tax ID | 99999999-9-99 | Alpha |
| Email | eszabo.eval-fixture@example.invalid | Alpha |
| Phone | +36 99 000 0001 | Alpha |
| IBAN | HU68 KAMU 0001 2345 6789 0123 4567 | Beta |
| Address | 9999 Tesztváros, Kamu utca 47., Floor 3 | Alpha |
| Auditor | Dr. Levente Varga | Alpha, Beta |
