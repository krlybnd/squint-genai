# QA image

Quality gates run **in this image**, not in ops. The container is a **one-shot**: default `CMD` is `make system-test`, then it exits.

```bash
docker compose --profile qa run --rm qa                 # system-test, then stop
docker compose --profile qa run --rm qa make unittest   # unit only, then stop
```

`network_mode: host` so the same localhost ports as the demo stack work (api `:8000`, chat `:8002`, UI `:5173`, Keycloak `:8080`). The Makefile does not call Docker.

`system-test` is **every measuring suite**: unit + coverage, API Gherkin, Playwright e2e, live retrieval IR, live DeepEval generation. Offline `tests/eval` dataset unittest is not a gate.

| Target | What |
|--------|------|
| `unittest` | All unit tests + combined coverage |
| `system-test` | All measuring tests (unit + API + e2e + live eval) |
| `api-test` | Live HTTP Gherkin in `tests/api` only |
| `e2e` | Playwright UI BDD in `tests/e2e` |
| `eval-live` | Live retrieval IR (no judge LLM) |
| `eval-live-generation` | Live DeepEval generation gate |
| `license` | CycloneDX SBOM merge + Grant (needs Docker on the **host**) |

## Live suites need a finished bootstrap

`system-test` (except the unit slice), `eval-live`, `eval-live-generation`, `api-test`, and `e2e` only work after Compose is up **and** ops is healthy. They are not in default CI ([ADR 007](../../docs/adr/007-no-live-tests-in-ci.md)).

## OpenAI key (DeepEval)

`eval-live-generation` (and therefore `system-test`) needs an OpenAI-compatible key for the judge. Compose loads it from `.env`; the qa container uses `env_file: .env`.
