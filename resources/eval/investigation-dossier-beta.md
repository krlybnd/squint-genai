---
title: "Investigation Dossier Beta — Financial Trace & Witness Transcript"
case_ref: "FIN-TRACE-2024/8812-B"
classification: "SYNTHETIC TEST MATERIAL — NOT A REAL INVESTIGATION"
generated: "2026-08-30"
language: "en"
pages_target: 10
related: "investigation-dossier-alpha.md (ART-2024/8812)"
---

# INVESTIGATION DOSSIER — BETA

## FIN-TRACE-2024/8812-B | Consolidated Financial Trace & Auditor Deposition

**Document type:** Financial intelligence trace memorandum (synthetic eval corpus)
**Prepared by:** Financial Forensics Unit — **FICTITIOUS AGENCY FOR TESTING ONLY**
**Date:** 28 June 2024
**Version:** 2.1 (eval edition)

---

> **MANDATORY NOTICE**
> AI-generated **test material** for Squint evaluation. **All companies, banks, IBANs, and account numbers are fictional** (Kamu* prefix).
> Cross-references Dossier Alpha (ART-2024/8812) by design for multi-document RAG goldens.

---

## Table of Contents

1. Executive Summary
2. Purpose and Link to Alpha Referral
3. Banking & Transfer Analysis
4. Entity Graph
5. Witness Transcript — Dr. Levente Varga
6. Operational Role of Esther Szabo
7. Timeline Reconciliation
8. Counterparty Screening
9. Decoy Exclusion Notes
10. Appendices

---

## 1. Executive Summary

This memorandum consolidates **banking evidence** supporting Dossier Alpha’s procurement fraud referral **ART-2024/8812**. Forensic accountants traced **HUF 47.2 million** through **Kamuhold Beruházási Zrt.** (registration **99-99-884422**) into Kamubank account **99990001-00000001**, with material activity on **2024-04-12**.

Key confirmations:

| Element | Beta confirmation |
|---------|-------------------|
| Shell entity | Kamuhold Beruházási Zrt. — same reg. as Alpha |
| Account | Kamubank 99990001-00000001 |
| Amount | HUF 47.2M aggregate inflow cluster |
| Date | 2024-04-12 primary transfer |
| Witness | Dr. Levente Varga deposition 2024-06-20 |
| Natural person | Esther Szabo — operational approvals per Alpha §3.2 |

**IBAN (international format, fictional):** **HU68 KAMU 0001 2345 6789 0123 4567** — matches Kamubank domestic routing for trace export.

This dossier **does not** analyse the 2023 environmental penalty against Kamuhold **Építő** Kft. (see Gamma decoy). Similar corporate prefix “Kamuhold” is a deliberate retrieval trap.

---

## 2. Purpose and Link to Alpha Referral

Beta was opened when KAH liaison matched internal audit case **ART-2024/8812** to SWIFT monitoring alert **MON-2024-0412-7788**. Scope: verify whether Kamuhold consulting payments (Alpha Exhibit A-9) represent circular flows.

Legal hooks cited (corpus noise):

- **Act LIII of 2017** on anti-money laundering — §§ 56–61 reporting (hypothetical SAR draft not included);
- **Act C of 2012** Criminal Code — money laundering **Section 303** referenced abstractly;
- **EU Directive 2015/849** (4AMLD) recital 39 — beneficiary identification.

Investigators had **no access** to KamuBridge internal ledger — abstention goldens may ask about KamuBridge offshore accounts (not in corpus).

---

## 3. Banking & Transfer Analysis

### 3.1 Account profile — Kamubank 99990001-00000001

| Attribute | Detail |
|-----------|--------|
| Account holder | Kamuhold Beruházási Zrt. |
| Branch | Kamubank 9999 — Tesztváros central (fictional) |
| Currency | HUF primary; EUR sub-ledger empty Q2 |
| Open date | 2023-12-01 |
| Status at trace date | Active, partial freeze recommended |

### 3.2 April 2024 cluster

| Date | Direction | Counterparty | Amount (HUF) | Reference |
|------|-----------|--------------|-------------:|-----------|
| 2024-04-05 | IN | KamuBridge Szolgáltató Zrt. | 12,400,000 | HI-2024/031 |
| 2024-04-12 | IN | KamuBridge Szolgáltató Zrt. | 18,100,000 | HI-2024/038 |
| 2024-04-12 | OUT | Fragment A (see §3.3) | 14,000,000 | TR-8812-A |
| 2024-04-19 | IN | KamuBridge Szolgáltató Zrt. | 18,100,000 | duplicate posting corrected |
| 2024-05-28 | IN | KamuBridge Szolgáltató Zrt. | 16,700,000 | HI-2024/044 |

**Aggregate inflow Q2 (Kamuhold consulting):** **HUF 47.2M** — reconciles Alpha §6.3 kickback tranche definition.

### 3.3 Outbound fragments (partial)

On **2024-04-12**, three outbound payments totalling HUF 14.0M:

1. HUF 6.2M → **KamuTanács Kft.** (reg. 99-99-771199) — nominee consultancy;
2. HUF 4.1M → cash withdrawal Kamubank branch 9999-044;
3. HUF 3.7M → **Esther Szabo** personal account ending **8891** (tax ID **99999999-9-99**) — flagged as potential unjust enrichment.

Remaining balance retained through May — further tracing ongoing in eval narrative.

### 3.4 IBAN validation

HU68 KAMU 0001 2345 6789 0123 4567 — checksum valid under ISO 13616 test rules for **fictional** eval data only.

---

## 4. Entity Graph

```
KamuBridge Szolgáltató Zrt.
        │ (consulting invoices)
        ▼
Kamuhold Beruházási Zrt. [99-99-884422]
        │ Kamubank 99990001-00000001
        ├──► KamuTanács Kft.
        ├──► cash withdrawal
        └──► Esther Szabo (personal acct …8891)
```

**Dr. Levente Varga** sits outside the graph as independent auditor — attests to circular pattern in deposition §5.

**Not in graph:** Kamuhold Építő Kft. (Gamma), KamuLine Kft. (vendor predecessor), environmental penalty payee.

---

## 5. Witness Transcript — Dr. Levente Varga

**Date:** 2024-06-20
**Location:** Fictional Office of Internal Audit, Room 4.12
**Case:** FIN-TRACE-2024/8812-B / ART-2024/8812
**License:** AV-2011-4488 (eval persona)

**Q:** State your role.
**A:** I am an external auditor engaged 2024-02-10 to review margin recognition on FA-2023/114 change orders.

**Q:** What prompted your 2024-05-03 memorandum?
**A:** I saw consulting fees to **Kamuhold Beruházási Zrt.** without mapped deliverables in the project WBS. Invoices HI-2024/031, 038, and 044 totalled **forty-seven point two million forints**, paid across April and May 2024.

**Q:** Did you examine Kamubank account **99990001-00000001**?
**A:** Only through redacted bank confirmation provided by internal audit on 2024-06-01. A significant inbound on **twelve April 2024** matched invoice HI-2024/038.

**Q:** Did Esther Szabo appear in your testing?
**A:** Yes. She approved all three Kamuhold invoices unusually quickly. Her tax ID **99999999-9-99** appears on delegation logs I reviewed — I do not allege criminal conduct; I report accounting anomalies.

**Q:** Any link to environmental case KAH-KV-2023/4419?
**A:** None in my workpapers. Different company — **Builder**, not **Investment**.

**Q:** Exhibit reference?
**A:** Alpha Exhibit A-7; Beta Exhibit B-4 bank redaction.

Transcript ends — eval corpus does not include cross-examination on Fifth Amendment equivalents.

---

## 6. Operational Role of Esther Szabo

Consolidated from Alpha and bank SWIFT metadata:

| PO | Date | Vendor | Amount (HUF) | Szabo approval latency |
|----|------|--------|-------------:|------------------------|
| PO-4471 | 2024-04-04 | Kamuhold | 12,400,000 | 11 min |
| PO-4488 | 2024-04-18 | Kamuhold | 18,100,000 | 9 min |
| PO-4498 | 2024-05-27 | Kamuhold | 16,700,000 | 14 min |

Contact on file: **eszabo.eval-fixture@example.invalid**, **+36 99 000 0001**, **9999 Tesztváros, Kamu utca 47., Floor 3**.

Szabo’s Q2 cumulative authorised spend **HUF 182M** (Alpha §3.2) — Kamuhold subset is 25.9% of personal authority volume, statistical anomaly.

---

## 7. Timeline Reconciliation

| Alpha event | Beta banking evidence |
|-------------|----------------------|
| 2024-04-05 HI-2024/031 paid | IN 12.4M 2024-04-05 |
| 2024-04-12 checkpoint | IN 18.1M + OUT fragments 14.0M |
| 2024-04-19 HI-2024/038 | IN 18.1M (posting correction noted) |
| 2024-05-28 HI-2024/044 | IN 16.7M |
| 2024-06-07 KAH ART-2024/8812 | MON alert predates registry entry by 48h |

Discrepancy note: Alpha lists second invoice **2024-04-19** while bank shows **2024-04-12** primary posting — resolved as bank value date vs ERP accrual date (Appendix B).

---

## 8. Counterparty Screening

### 8.1 Kamuhold Beruházási Zrt.

- Sanctions lists: no hit (fictional screening);
- PEP database: nominee director low confidence hit — inconclusive;
- Media: zero substantive coverage Q2 2024.

### 8.2 Kamuhold Építő Kft. (decoy exclusion)

| Field | Builder (Gamma) | Investment (Alpha/Beta) |
|-------|-----------------|-------------------------|
| Reg. | 99-99-991133 | 99-99-884422 |
| Case | KAH-KV-2023/4419 env. | ART-2024/8812 procurement |
| Amount | HUF 47M penalty | HUF 47.2M consulting |
| Year | 2023 | 2024 |

Eval goldens must **not** treat Builder penalty as criminal kickback.

---

## 9. Decoy Exclusion Notes

Questions designed to fail if Gamma is retrieved incorrectly:

1. “What **criminal** statute applies to the HUF 47M Kamuhold **environmental** fine?” → **Abstain** — criminal classification not in Alpha/Beta.
2. “Did Esther Szabo appear in the **2023** environmental inspection?” → **Abstain** — Szabo not in Gamma.
3. “Is Kamuhold **Építő** the shell in ART-2024/8812?” → **No** — Beruházási Zrt.

---

## 10. Appendices

### Appendix A — SWIFT field mapping (redacted)

Field 50K: Kamuhold Beruházási Zrt.
Field 59: KamuBridge Szolgáltató Zrt.
Field 70: `/INV/HI-2024/038`

### Appendix B — ERP vs bank date reconciliation

Two-day lag on HI-2024/038 — accrual policy AP-044.

### Appendix C — Statistical noise paragraph

Lorem-adjacent legal boilerplate on **Act XXV of 2009** data retention — no operative fact. Retrieval systems must rank §3–§6 above this appendix.

### Appendix E — KamuTanács Kft. profile

Registration 99-99-771199. Declared activity: business coaching. Received HUF 6.2M from Kamuhold 2024-04-12. No employees listed. Address 9999 Tesztváros, Mellék utca 22. (fictional). No link to Esther Szabo home address on Kamu utca.

### Appendix F — Cash withdrawal analysis

HUF 4.1M cash withdrawal Kamubank branch 9999-044 on 2024-04-12 15:18. CCTV retention policy 90 days — expired before investigators reviewed. Identity of withdrawer not in corpus.

### Appendix G — Personal account …8891

Esther Szabo inbound HUF 3.7M same day. Account masked in public summary; tax ID **99999999-9-99** links ownership in internal worksheet B-7 (eval PII for vault tests).

### Appendix H — KamuBridge payment instruction memo

KamuBridge treasury memo NBS-2024-0412 authorises three tranches to Kamuhold matching invoice numbers HI-2024/031, 038, 044. Memo signed Martin Kovács. Does not explain commercial rationale — abstention if asked “why KamuBridge paid Kamuhold” beyond circular consulting theory.

### Appendix I — MON alert technical fields

Alert MON-2024-0412-7788 triggered on velocity rule R-VEL-12: three inbound > HUF 10M within 30 days to same shell entity category. False positive rate for rule 8.2% in calibration quarter — human review opened Beta case.

### Appendix J — Joint Alpha-Beta finding checklist

Investigators sign-off (fictional):

- [x] F-01 Kamuhold Beruházási Zrt. 99-99-884422
- [x] F-02 Kamubank 99990001-00000001
- [x] F-03 Dr. Levente Varga testimony
- [x] F-04 Q2 2024 window
- [x] F-05 HUF 47.2M aggregate
- [x] F-06 Esther Szabo 99999999-9-99
- [x] F-07 KAH ART-2024/8812

### Appendix K — Legal noise block (long)

Discussion of **EU Regulation 2016/679** lawful basis for processing witness data — Art. 6(1)(f) legitimate interest. Repeats **4AMLD** travel rule irrelevant to domestic HUF transfer. Cites **FATF Recommendation 24** on beneficial ownership — Kamuhold BO unresolved. No operative finding.

### Appendix L — Interview scheduling log

2024-06-10 Szabo no-show. 2024-06-25 rescheduled — outcome not in corpus. Dr. Varga deposition completed 2024-06-20 (§5).

### Appendix M — IBAN extended validation log

HU68 KAMU 0001 2345 6789 0123 4567 — MOD-97 check pass. BIC KAMUHUXX (fictional test BIC). Used for export to fictional Europol liaison — no real submission.

### Appendix N — Price uplift methodology

Regression compared KamuLine baseline SKUs to KamuBridge post-CR prices. Control group: SKUs not affected by CR-2024/04. Uplift statistically significant at α=0.01 for NET and SIEM categories.

### Appendix O — Split invoice anti-control pattern

Three Kamuhold invoices each below HUF 25M dual-approval threshold but aggregate HUF 47.2M exceeds policy intent — cited in Alpha §8 preliminary assessment.

---

## 11. Consolidated Trace Narrative (Extended)

Beta memorandum FIN-TRACE-2024/8812-B exists to translate auditor language into bank-confirmed fact. Where Alpha describes policy breaches and invoice anomalies, Beta answers whether money actually moved, when, and to whom. The April 2024 cluster on Kamubank **99990001-00000001** is the evidentiary anchor: three inbound credits from KamuBridge Szolgáltató Zrt. totalling **HUF 47.2 million**, followed by partial outbound fragmentation including KamuTanács Kft., a cash withdrawal, and a credit to Esther Szabo’s personal account.

Dr. Levente Varga’s deposition (§5) supplies human-readable confirmation without exposing full bank statements. Varga explicitly denies any connection between his work and the 2023 environmental enforcement against Kamuhold **Építő** Kft. — a decoy exclusion repeated because retrieval systems often conflate “Kamuhold” string matches. Evaluators scoring cross-document synthesis should require **Beruházási Zrt.** registration **99-99-884422** before awarding credit for shell-company findings.

IBAN **HU68 KAMU 0001 2345 6789 0123 4567** appears in export formats for liaison purposes; domestic routing maps to the same Kamubank branch documented in Alpha §6.2. No IBAN in Gamma dossier — environmental payments used KAH collection account **99994008-00000001**.

Timeline reconciliation (§7) resolves ERP-vs-bank date skew on invoice HI-2024/038. Generation answers should prefer bank dates when question specifies “transfer date” and ERP dates when question specifies “invoice approval.”

MON alert MON-2024-0412-7788 illustrates how automated monitoring intersects manual referral ART-2024/8812. Alert metadata in Appendix I is retrieval noise unless question asks specifically for rule identifiers.

This dossier completes cross-doc findings F-01 through F-07 listed in `resources/eval/README.md`. It does not extend to KamuBridge offshore structures, KamuLine civil claims, or criminal sentencing — none appear in corpus.

---

**END OF DOSSIER BETA**

_FIN-TRACE-2024/8812-B — synthetic eval corpus v2.1 — 2026-08-30_
