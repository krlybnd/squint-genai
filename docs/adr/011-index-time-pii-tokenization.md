# ADR 011: Index-time PII tokenization + tenant vault

## Context

Chat guardrails mask user queries and retrieved chunks before the LLM, but **indexing** still sends raw PDF text to the embedding provider (LiteLLM/OpenAI) during semantic chunking and dense vector upsert. Qdrant payloads also store plaintext `text`. For contract-like documents this leaks exact party names, emails, and financial identifiers to external providers and the vector store.

Operators asked for tenant-scoped storage where authorized users can see plaintext while external systems see only tokens.

## Decision

1. **Index-time tokenization (feature-flagged):** Before `SemanticSplitterNodeParser` runs, Presidio Analyzer detects entities; spans are replaced with deterministic typed tokens (`<PERSON_a1b2c3d4>`). Only tokenized text is chunked, embedded, and stored in Qdrant.

2. **Tenant vault in Postgres:** Table `pii_vault_entries` stores `token → Fernet ciphertext`. Row-level `tenant_id` isolation matches existing repository patterns. Plaintext never appears in SQL columns.

3. **Encryption (Phase 1):** Single global `VAULT_ENCRYPTION_KEY` (Fernet) + separate `VAULT_TOKEN_SALT` for HMAC token derivation. Wrapped behind a `Cipher` protocol so KMS / Vault Transit can replace Fernet later without changing vault callers.

4. **Detokenize API only:** `POST /v1/vault/detokenize` with `AppRole.READ` + tenant filter. Unknown or cross-tenant tokens are omitted (no existence oracle). Audit log per request (user, tenant, token count — never values).

5. **Feature flag:** `INDEXING_PII_TOKENIZATION_ENABLED=false` by default. Requires `guardrails` profile (Presidio analyzer reachable).

## Trade-offs

| Choice | Benefit | Cost |
|--------|---------|------|
| Deterministic tokens | Same value → same token across chunks/docs; retrieval (BM25 + dense) still works | Equality/frequency leakage (same token implies same value) |
| Typed tokens vs `****` | Preserves semantic signal for search | Token format reveals entity class |
| Global Fernet key | Simple dev/prod bootstrap | Weaker than per-tenant DEK + KMS envelope |
| MinIO unchanged | Smaller slice | Original PDF remains plaintext in object storage |
| Presidio detect-only | Reuses existing sidecar | Missed entities still leak; custom recognizers are follow-up |

## Consequences

- New Alembic revision `003`, shared `domains/pii_vault/` + `crosscut/crypto/`
- Indexing worker needs sync Analyzer client + vault write repo
- API gains vault module; chat citations show tokenized text until UI detokenizes
- Acceptance tests under `@guardrails` with flag enabled

## Follow-up (Phase 2)

- MinIO SSE-C / app-level PDF encryption
- Per-tenant DEK + KMS / HashiCorp Vault Transit
- Vault entry cleanup on document delete

HU/contract regex supplements ship in `domains/pii_vault/extra_recognizers.py` (index + query paths).
Query tokenization + SSE detokenize ship behind `PII_VAULT_ENABLED`.
