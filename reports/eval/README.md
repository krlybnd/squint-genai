# Eval reports

Committed **live snapshots** from manual eval runs. Refresh locally — not CI ([ADR 007](../../docs/adr/007-no-live-tests-in-ci.md)).

Full case list, metric glossary, and run instructions: [`tests/eval/README.md`](../../tests/eval/README.md).

Each file starts with `_Run: …_`. DeepEval promotes timestamped exports to stable filenames (e.g. `investigation-generation.md`).

## Default profile (demo PDF)

| Report | Last run | Tier | Source |
|--------|----------|------|--------|
| [retrieval.md](retrieval.md) | 2026-08-27 21:05:27 +0200 | R1 IR | Pydantic Evals |
| [generation.md](generation.md) | 2026-08-27 21:12:07 | G2 | DeepEval Faithfulness + Answer Relevancy |

## Investigation profile (`resources/eval/` corpus)

| Report | Last run | Tier | Headline |
|--------|----------|------|----------|
| [investigation-retrieval.md](investigation-retrieval.md) | 2026-08-30 16:43:25 +0200 | R1 | Recall@5 **1.00**, Precision@5 **0.53** (gate 0.85) |
| [investigation-generation.md](investigation-generation.md) | 2026-08-30 17:07:56 | G2 | Pass rate **44%** (4/9 labeled); 2/3 abstention |
| [guardrails.md](guardrails.md) | 2026-08-30 (latest) | S1 | Attack block **100%**, benign pass **80%** (IBAN DeBERTa FP); overdefense blocked |

Refresh:

```bash
make eval-live-investigation
make eval-live-investigation-generation
make up-guardrails && make eval-live-guardrails
```
