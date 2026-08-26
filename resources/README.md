# Sample documents

Text-based PDFs for local RAG demos (upload in the UI or via the API). They are **not committed** — download them with:

```bash
make resources
```

The live eval suite (`make eval-live`) uses goldens in [`tests/eval/dataset.json`](../tests/eval/dataset.json) written against these files — index them before running the gate. All files are redistributable; see sources below.

| File | Pages | What to ask |
|------|------:|-------------|
| `attention-is-all-you-need.pdf` | 15 | What is multi-head attention? BLEU scores? |
| `rag-lewis-2020.pdf` | 19 | How does RAG-Sequence differ from RAG-Token? |
| `us-constitution.pdf` | 20 | How is the President elected? What is Article I about? |
| `nasa-fy2025-mission-fact-sheets.pdf` | 33 | What is Artemis II? What does Orion do? |
| `nist-ai-rmf-1.0.pdf` | 48 | What are the four AI RMF functions? |

EUR-Lex (GDPR / EU AI Act) blocked automated download (WAF challenge). Use those from the browser if you want a legal corpus.

## Sources and licenses

| File | Source | License / terms |
|------|--------|-----------------|
| `attention-is-all-you-need.pdf` | [arXiv:1706.03762](https://arxiv.org/abs/1706.03762) (Vaswani et al.) | arXiv non-exclusive distribution license |
| `rag-lewis-2020.pdf` | [arXiv:2005.11401](https://arxiv.org/abs/2005.11401) (Lewis et al.) | arXiv non-exclusive distribution license |
| `us-constitution.pdf` | [Congress.gov literal print](https://constitution.congress.gov/static/files/Literal_Print_of_Constitution_MCT_1.9.26.pdf) | U.S. government work, public domain |
| `nasa-fy2025-mission-fact-sheets.pdf` | [NASA](https://www.nasa.gov/wp-content/uploads/2024/03/nasa-fiscal-year-2025-mission-fact-sheets.pdf) | U.S. government work, public domain |
| `nist-ai-rmf-1.0.pdf` | [NIST AI 100-1](https://doi.org/10.6028/NIST.AI.100-1) | U.S. government work, public domain |

arXiv papers remain copyright of their authors; included here only as a local demo corpus. Do not rehost them as your own work.
