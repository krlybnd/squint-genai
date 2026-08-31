# Retrieval IR

_Run: 2026-08-31 14:26:29 +0200_

Pydantic Evals · k=5 · 9 labeled goldens.

| Metric | Score | Gate |
|---|---:|---:|
| Hit Rate@5 | 1.00 | 0.90 |
| Recall@5 | 0.89 | 0.90 |
| Precision@5 | 0.76 | 0.85 |
| MRR | 0.94 | 0.80 |
| nDCG@5 | 0.93 | 0.80 |

## Cases

| Case | Query | Expected | Top sources | Hit | Recall | Precision | MRR | nDCG |
|---|---|---|---|---:|---:|---:|---:|---:|
| 01:Which shell company appears in both the procurement fraud referral an... | Which shell company appears in both the procurement fraud referral and the financial trace dossier, and what is its company registration number? | investigation-dossier-alpha.md, investigation-dossier-beta.md | investigation-dossier-alpha.pdf, investigation-dossier-beta.pdf, investigation-dossier-alpha.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 02:What Kamubank account received the consolidated HUF 47.2M trace in Ap... | What Kamubank account received the consolidated HUF 47.2M trace in April 2024, and on what date did that transfer cluster occur? | investigation-dossier-alpha.md, investigation-dossier-beta.md | investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-alpha.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-beta.pdf | 1.00 | 1.00 | 0.80 | 1.00 | 0.98 |
| 03:Who is the auditor witness named in both investigation materials? | Who is the auditor witness named in both investigation materials? | investigation-dossier-alpha.md, investigation-dossier-beta.md | investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-alpha.pdf, investigation-dossier-alpha.pdf | 1.00 | 1.00 | 0.80 | 1.00 | 0.96 |
| 04:What is Esther Szabo's tax identification number in the procurement i... | What is Esther Szabo's tax identification number in the procurement investigation? | investigation-dossier-alpha.md, investigation-dossier-beta.md | investigation-dossier-alpha.pdf, investigation-dossier-alpha.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-beta.pdf, investigation-dossier-gamma-decoy.pdf | 1.00 | 1.00 | 0.60 | 1.00 | 0.97 |
| 05:What KAH case reference is logged for the procurement fraud referral? | What KAH case reference is logged for the procurement fraud referral? | investigation-dossier-alpha.md, investigation-dossier-beta.md | investigation-dossier-alpha.pdf, investigation-dossier-alpha.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-alpha.pdf | 1.00 | 0.50 | 0.60 | 1.00 | 0.95 |
| 06:What aggregate HUF amount is traced as hidden commission in Q2 2024? | What aggregate HUF amount is traced as hidden commission in Q2 2024? | investigation-dossier-alpha.md, investigation-dossier-beta.md | investigation-dossier-alpha.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-alpha.pdf | 1.00 | 1.00 | 0.80 | 1.00 | 0.90 |
| 07:What IBAN appears in the financial trace export for the intermediary ... | What IBAN appears in the financial trace export for the intermediary account? | investigation-dossier-beta.md | investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-alpha.pdf | 1.00 | 1.00 | 0.80 | 1.00 | 1.00 |
| 08:Is Kamuhold Építő Kft. the shell company in case ART-2024/8812? If no... | Is Kamuhold Építő Kft. the shell company in case ART-2024/8812? If not, which entity and company registration is? | investigation-dossier-alpha.md, investigation-dossier-beta.md | investigation-dossier-gamma-decoy.pdf, investigation-dossier-beta.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf | 1.00 | 0.50 | 0.60 | 0.50 | 0.68 |
| 09:What penalty amount was assessed against Kamuhold Építő Kft. in 2023,... | What penalty amount was assessed against Kamuhold Építő Kft. in 2023, and under which case reference? | investigation-dossier-gamma-decoy.md | investigation-dossier-gamma-decoy.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-beta.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-gamma-decoy.pdf | 1.00 | 1.00 | 0.80 | 1.00 | 0.96 |

## Index catalog

3 indexed document(s).

No duplicate filenames, mixed stems, or missing expected sources.
