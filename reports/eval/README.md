# Eval reports

Committed live snapshots. Refresh with `make eval-live` and `make eval-live-generation` — not CI ([ADR 007](../../docs/adr/007-no-live-tests-in-ci.md)).

Each file starts with `_Run: …_`. DeepEval stamps generation as `YYYYMMDD_HHMMSS` in the export filename; that time is copied onto [generation.md](generation.md).

| Report | Last run | Source |
|--------|----------|--------|
| [retrieval.md](retrieval.md) | 2026-08-27 21:05:27 +0200 | Pydantic Evals IR |
| [generation.md](generation.md) | 2026-08-27 21:12:07 | DeepEval Faithfulness + Answer Relevancy |
