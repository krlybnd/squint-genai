# Retrieval IR

_Run: 2026-08-27 21:05:27 +0200_

Pydantic Evals · k=5 · 20 labeled goldens.

| Metric | Score | Gate |
|---|---:|---:|
| Recall@5 | 1.00 | 0.75 |
| Precision@5 | 1.00 | 0.45 |
| Hit Rate@5 | 1.00 | 0.75 |
| MRR | 1.00 | 0.65 |
| nDCG@5 | 1.00 | 0.65 |

## Cases

| Case | Query | Expected | Top sources | Recall | MRR | nDCG |
|---|---|---|---|---:|---:|---:|
| 01:What architecture does Attention Is All You Need propose instead of r... | What architecture does Attention Is All You Need propose instead of recurrence and convolution? | attention-is-all-you-need.pdf | attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf | 1.00 | 1.00 | 1.00 |
| 02:In the Transformer base model, how many attention heads are used and ... | In the Transformer base model, how many attention heads are used and what is the dimension d_k of each head? | attention-is-all-you-need.pdf | attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf | 1.00 | 1.00 | 1.00 |
| 03:What BLEU scores did the big Transformer report on WMT 2014 English-t... | What BLEU scores did the big Transformer report on WMT 2014 English-to-German and English-to-French? | attention-is-all-you-need.pdf | attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf | 1.00 | 1.00 | 1.00 |
| 04:How does the Transformer encode token order without recurrence? | How does the Transformer encode token order without recurrence? | attention-is-all-you-need.pdf | attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf, attention-is-all-you-need.pdf | 1.00 | 1.00 | 1.00 |
| 05:How does RAG-Sequence differ from RAG-Token in the Lewis et al. 2020 ... | How does RAG-Sequence differ from RAG-Token in the Lewis et al. 2020 RAG paper? | rag-lewis-2020.pdf | rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf | 1.00 | 1.00 | 1.00 |
| 06:What parametric generator and non-parametric memory does RAG combine? | What parametric generator and non-parametric memory does RAG combine? | rag-lewis-2020.pdf | rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf | 1.00 | 1.00 | 1.00 |
| 07:When is RAG-Sequence preferable to RAG-Token according to the RAG paper? | When is RAG-Sequence preferable to RAG-Token according to the RAG paper? | rag-lewis-2020.pdf | rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf | 1.00 | 1.00 | 1.00 |
| 08:What corpus does the original RAG paper retrieve documents from? | What corpus does the original RAG paper retrieve documents from? | rag-lewis-2020.pdf | rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf, rag-lewis-2020.pdf | 1.00 | 1.00 | 1.00 |
| 09:What does Article I of the United States Constitution establish? | What does Article I of the United States Constitution establish? | us-constitution.pdf | us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf | 1.00 | 1.00 | 1.00 |
| 10:How is the President of the United States chosen under the Constitution? | How is the President of the United States chosen under the Constitution? | us-constitution.pdf | us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf | 1.00 | 1.00 | 1.00 |
| 11:What rights does the First Amendment protect? | What rights does the First Amendment protect? | us-constitution.pdf | us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf | 1.00 | 1.00 | 1.00 |
| 12:How can the United States Constitution be amended? | How can the United States Constitution be amended? | us-constitution.pdf | us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf | 1.00 | 1.00 | 1.00 |
| 13:How many Senators does each state have, and how long is a Senate term? | How many Senators does each state have, and how long is a Senate term? | us-constitution.pdf | us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf, us-constitution.pdf | 1.00 | 1.00 | 1.00 |
| 14:What is the purpose of NASA's Artemis II mission? | What is the purpose of NASA's Artemis II mission? | nasa-fy2025-mission-fact-sheets.pdf | nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf | 1.00 | 1.00 | 1.00 |
| 15:What is the Orion spacecraft used for in NASA's Artemis program? | What is the Orion spacecraft used for in NASA's Artemis program? | nasa-fy2025-mission-fact-sheets.pdf | nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf | 1.00 | 1.00 | 1.00 |
| 16:What launch vehicle sends Orion toward the Moon in the Artemis program? | What launch vehicle sends Orion toward the Moon in the Artemis program? | nasa-fy2025-mission-fact-sheets.pdf | nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf, nasa-fy2025-mission-fact-sheets.pdf | 1.00 | 1.00 | 1.00 |
| 17:What are the four functions of the NIST AI Risk Management Framework? | What are the four functions of the NIST AI Risk Management Framework? | nist-ai-rmf-1.0.pdf | nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf | 1.00 | 1.00 | 1.00 |
| 18:Is the NIST AI Risk Management Framework a mandatory regulation? | Is the NIST AI Risk Management Framework a mandatory regulation? | nist-ai-rmf-1.0.pdf | nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf | 1.00 | 1.00 | 1.00 |
| 19:What characteristics of trustworthy AI does the NIST AI RMF list? | What characteristics of trustworthy AI does the NIST AI RMF list? | nist-ai-rmf-1.0.pdf | nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf | 1.00 | 1.00 | 1.00 |
| 20:What is the GOVERN function responsible for in the NIST AI RMF? | What is the GOVERN function responsible for in the NIST AI RMF? | nist-ai-rmf-1.0.pdf | nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf, nist-ai-rmf-1.0.pdf | 1.00 | 1.00 | 1.00 |
