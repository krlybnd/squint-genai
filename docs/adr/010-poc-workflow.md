# ADR 010: PoC workflow under `pocs/`

## Context

We explore infra/model options before product wiring. Ad-hoc checks lose the
questions we cared about; heavy shared libs and rigid metric schemas add friction.

## Decision

- PoCs live under `pocs/<snake_name>/` and are listed in `project.cue`.
- **Required:** `poc.md` (from `.cursor/skills/poc/templates/poc.md.j2`) and
  `scripts/poc.sh` (from the skill skeleton).
- **`poc.sh` is thin:** start harness, health, a few proof calls, optional resource
  snapshot. Stdout is teed to **`results/result.log`** (gitignored) as light evidence.
- **No shared PoC lib** and **no fixed result schema** — the log is the proof.
- **`results/` and `run/` are never committed.**
- Not a CI gate; not part of the root product compose stack.
- Agent playbook: `.cursor/skills/poc/`.

## Consequences

- Decisions live in `poc.md`; re-runs only refresh the local proof log.
- Productizing a PoC remains a separate issue/PR.
- Changes under `pocs/` or `.cursor/` alone do not start CI (`paths-ignore`) or
  local pre-commit (top-level `exclude` + no `always_run` workspace lint).
  Touching `project.cue` / product trees still does.
