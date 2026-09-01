# Presidio analyzer (PII detect)

Default Compose stack (PII vault is on). Internal DNS: `presidio-analyzer:3000`.

Used by shared `AnalyzerClient` (`ANALYZER_API_BASE`) and optionally by LiteLLM's built-in `presidio-pii` guardrail.

## Detection limits

The default recognizer set is far too broad for a document corpus: `DATE_TIME` and the
`US_*` recognizers claim fragments of Hungarian identifiers, so one IBAN or tax number
ends up split across a vault token and leftover plaintext. Three settings constrain it.

| Env | Default | Purpose |
|-----|---------|---------|
| `ANALYZER_ENTITIES` | `PERSON,EMAIL_ADDRESS,PHONE_NUMBER,IBAN_CODE,CREDIT_CARD,IP_ADDRESS` | Entity types Presidio may return. Empty means every built-in recognizer. |
| `ANALYZER_SCORE_THRESHOLD` | `0.3` | Drops low-confidence hits (`US_BANK_NUMBER` scores 0.05, `US_DRIVER_LICENSE` 0.01). |
| `ANALYZER_ALLOW_LIST` | empty | Regex patterns never treated as PII. A pattern also clears the longer span containing it, so `Kamu` clears `Kamuhold Beruházási Zrt.` |

Hungarian identifiers are matched by the contract regexes in
`agentic_shared.domains.pii_vault.extra_recognizers`, which take the span from any
analyzer hit they overlap so each identifier stays a single token.

Changing any of these requires a **reindex** — tokens are derived from the detected span,
so old chunks keep the old tokenization.
