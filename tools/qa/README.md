# QA recipes

Host Make targets for quality gates. Included from the root Makefile (`make unittest`, `make system-test`, …). These do **not** run inside the ops image.

`unittest` walks every project unit suite and always writes the **combined** coverage HTML under `.reports/coverage/combined/`. There is no lighter / per-project coverage switch at this layer.

| Target | What |
|--------|------|
| `unittest` | All unit tests + combined coverage |
| `system-test` | Live HTTP Gherkin in `tests/api` |
| `license` | CycloneDX SBOM merge + Grant |
| `eval-test` | Offline eval dataset checks in `tests/eval` |
| `eval-live` | Live retrieval IR (no judge LLM) |
| `eval-live-generation` | Live DeepEval generation gate |
| `e2e` | Playwright UI BDD in `tests/e2e` |

## Live suites need a finished bootstrap

`system-test`, `eval-live`, `eval-live-generation`, and `e2e` only work after Compose is up **and** ops bootstrap has finished. Wait until `docker compose ps` shows **ops** healthy (`make initialization` then `make bootstrap`). They are not in default CI ([ADR 007](../../docs/adr/007-no-live-tests-in-ci.md)).

## OpenAI key (DeepEval)

`eval-live-generation` needs an OpenAI-compatible key for the judge (also accepted as `EVAL_OPENAI_API_KEY` or `LITELLM_MASTER_KEY` — see `tests/eval/.env.example`).

Export in the shell that runs Make:

```bash
export OPENAI_API_KEY=sk-your-key
make eval-live-generation
```

Or pass `-e` into Compose (LiteLLM upstream, or any `exec`):

```bash
docker compose exec -e OPENAI_API_KEY=sk-your-key litellm true
OPENAI_API_KEY=sk-your-key docker compose up -d
```
