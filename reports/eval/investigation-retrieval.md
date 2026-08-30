# Retrieval IR

_Run: 2026-08-30 16:43:25 +0200_

Pydantic Evals · k=5 · 9 labeled goldens.

| Metric | Score | Gate |
|---|---:|---:|
| Recall@5 | 1.00 | 0.90 |
| Precision@5 | 0.53 | 0.85 |
| Hit Rate@5 | 1.00 | 0.90 |
| MRR | 0.89 | 0.80 |
| nDCG@5 | 0.90 | 0.80 |

## Cases

| Case | Query | Expected | Top sources | Recall | MRR | nDCG |
|---|---|---|---|---:|---:|---:|
| 01:Which shell company appears in both the procurement fraud referral an... | Which shell company appears in both the procurement fraud referral and the financial trace dossier? | investigation-dossier-alpha.md | investigation-dossier-alpha.pdf, investigation-dossier-alpha.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-alpha.pdf | 1.00 | 1.00 | 0.95 |
| 02:What Kamubank account received the consolidated HUF 47.2M trace in Ap... | What Kamubank account received the consolidated HUF 47.2M trace in April 2024? | investigation-dossier-beta.md | investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-alpha.pdf, investigation-dossier-gamma-decoy.pdf | 1.00 | 1.00 | 1.00 |
| 03:Who is the auditor witness named in both investigation materials? | Who is the auditor witness named in both investigation materials? | investigation-dossier-beta.md | investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-alpha.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-alpha.pdf | 1.00 | 1.00 | 1.00 |
| 04:What is Esther Szabo's tax identification number in the procurement i... | What is Esther Szabo's tax identification number in the procurement investigation? | investigation-dossier-alpha.md | investigation-dossier-alpha.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-gamma-decoy.pdf | 1.00 | 1.00 | 1.00 |
| 05:What KAH case reference is logged for the procurement fraud referral? | What KAH case reference is logged for the procurement fraud referral? | investigation-dossier-alpha.md | investigation-dossier-alpha.pdf, investigation-dossier-alpha.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-alpha.pdf | 1.00 | 1.00 | 0.95 |
| 06:What aggregate HUF amount is traced as hidden commission in Q2 2024? | What aggregate HUF amount is traced as hidden commission in Q2 2024? | investigation-dossier-alpha.md | investigation-dossier-beta.pdf, investigation-dossier-alpha.pdf, investigation-dossier-alpha.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf | 1.00 | 0.50 | 0.69 |
| 07:What IBAN appears in the financial trace export for the intermediary ... | What IBAN appears in the financial trace export for the intermediary account? | investigation-dossier-beta.md | investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf, investigation-dossier-beta.pdf | 1.00 | 1.00 | 1.00 |
| 08:Is Kamuhold Építő Kft. the shell company in case ART-2024/8812? | Is Kamuhold Építő Kft. the shell company in case ART-2024/8812? | investigation-dossier-alpha.md | investigation-dossier-beta.pdf, investigation-dossier-alpha.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-beta.pdf, investigation-dossier-gamma-decoy.pdf | 1.00 | 0.50 | 0.63 |
| 09:What penalty amount was assessed against Kamuhold Építő Kft. in 2023? | What penalty amount was assessed against Kamuhold Építő Kft. in 2023? | investigation-dossier-gamma-decoy.md | investigation-dossier-gamma-decoy.pdf, investigation-dossier-beta.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-gamma-decoy.pdf, investigation-dossier-gamma-decoy.pdf | 1.00 | 1.00 | 0.90 |
