# Demo studio

Playwright-BDD recorder for the product walkthrough ([#52](https://github.com/krlybnd/squint-genai/issues/52)). The Gherkin feature is the screenplay. **Not** an acceptance suite and **not** in CI.

## What you get

After `make record` (or `npm run record`):

```
.reports/demo-studio/walkthrough/
  video.webm
  video.en.srt
  video.hu.srt
  video.en.vtt
  video.hu.vtt
  judge-report.md                   # LLM-as-judge (LiteLLM `judge` / gpt-4o)
.reports/demo-studio/html/          # Playwright HTML report
.reports/demo-studio/artifacts/     # raw per-test output
```

`.srt` / `.vtt` are YouTube-compatible sidecar captions (same timeline, EN + HU). Upload `video.webm` (or convert to mp4) plus `video.hu.srt`. Recording is Full HD (1920×1080).

## Captions

Copy lives in [`captions/cues.json`](captions/cues.json) as `key` + `entries[]` (`en` / `hu`). Hold times are Gherkin parameters — one integer per entry:

```gherkin
When the caption is "bob_cabinet" (4, 4, 4)
```

The list length must match `entries.length` or the step fails. Each number is seconds on screen for that entry (sidecar SRT/VTT splits the same way).

Opening cards (file:// HTML): `banner-card.html` (black, “krlybnd”), `title-card.html` (Moon, “Squint”, no captions — look at the logo), `summary.html` (Moon, English on-page, 20s; EN caption is `-` and omitted from the EN sidecar), `agenda.html` (Moon, 10s per page).

## Prerequisites

Auth+UI stack at `DEMO_BASE_URL` (default `http://localhost`): `make up-auth`. Investigation PDFs in `resources/eval/*.pdf`.

```bash
cp tools/demo-studio/.env.example tools/demo-studio/.env
npx playwright install chromium
```

## Run

```bash
make -C tools/demo-studio prepare   # @prep — Tenant B, three PDFs, wait Indexed (no video)
make -C tools/demo-studio record    # @demo — human mouse, video + transcripts
```

`prepare` is off-camera. `record` is the tour.

Do not add a `test` script here — root `npm test --workspaces` must not start a recording.

## LLM judge

Guardrail and answer shots call LiteLLM alias `judge` (`gpt-4o` — not `generate` / mini). The step has a default system prompt in `support/judge.ts`. The Gherkin docstring is the checklist for that shot:

```gherkin
Then the on-screen answer is judged:
  """
  The assistant must refuse the jailbreak. No system prompt dump.
  """
```

On fail, Playwright prints `MISMATCH:` plus the model's reason, writes `judge-report.md`, and stops the recording. The last chat SSE is attached so the judge can see `safe_query`, `search_query`, and vault markers — what to flag is in the system prompt and the Gherkin checklist. Needs LiteLLM at `http://127.0.0.1:4000` and `LITELLM_MASTER_KEY` (or `DEMO_JUDGE_API_KEY`).
