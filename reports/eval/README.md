# Eval reports

Committed **live snapshots** from manual eval runs. Refresh locally — not CI ([ADR 007](../../docs/adr/007-no-live-tests-in-ci.md)).

Full case list, metric glossary, and run instructions: [`tests/eval/README.md`](../../tests/eval/README.md).

Live generation writes **DeepEval's own** timestamped markdown (`investigation-generation_YYYYMMDD_HHMMSS.md`, `investigation-abstention_*.md`). Retrieval prints to stdout — it does not wrap pydantic-evals in a custom markdown file.

Snapshots from **before 2026-08-30 evening** used Hit Rate as “Recall@k” and a single expected file per question. Later reports split Hit vs document Recall and score chunk Precision against a relevant **set**.

## Investigation corpus (`resources/eval/`)

| Report | Last run | Tier | Headline |
|--------|----------|------|----------|
| [investigation-retrieval.md](investigation-retrieval.md) | 2026-08-31 14:26:29 +0200 | R1 | Hit@5 **1.00**, document Recall@5 **0.89** (gate 0.90 miss), chunk Precision@5 **0.76** (gate 0.85 miss), MRR 0.94, nDCG 0.93 |
| [investigation-generation.md](investigation-generation.md) | 2026-08-31 17:56:08 | G2 | 9/9 labeled. Correctness **0.83**; Faithfulness **1.00**; Relevancy **1.00**; phrases 9/9 |
| [investigation-abstention.md](investigation-abstention.md) | 2026-08-31 17:56:15 | A0 | 3/3 clean refusal |

The 2026-08-31 jump came from constraining the Presidio analyzer (see
[`operations/presidio-analyzer/README.md`](../../operations/presidio-analyzer/README.md)).
Until then `DATE_TIME` swallowed `2024-04-12` outright and split the IBAN into fragments,
so several goldens were unanswerable regardless of the model or the prompt.

Older [`retrieval.md`](retrieval.md) / [`generation.md`](generation.md) / [`guardrails.md`](guardrails.md) are leftover (demo-PDF profile / sidecar llm-guard HTTP eval).

Refresh:

```bash
make eval-live
make eval-live-generation
```
