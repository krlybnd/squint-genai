# ADR 008: Repo metadata in CUE (`project.cue`)

## Context

Squint is a large monorepo: Python services, a shared library, React apps, live test
suites, infra configs, and extensive ADR/cursor-rule documentation. Agents and new
contributors must quickly learn **what each top-level path is for** and **what must not
go there** — without re-deriving structure from grep or stale prose.

We already maintain overlapping metadata:

- `make/projects.mk` — CI/Makefile fan-out project lists
- `.cursor/rules/` — agent coding conventions and scope
- `docs/` + ADRs — architectural *decisions* (why), not a live directory map

**Drift** is the main risk: a new folder or service lands in the repo but metadata
lags, misleading agents and reviewers.

[CUE](https://cuelang.org/) gives a typed, validatable schema for repo metadata:
folder purpose, stack, phase, ADR links, and `mustNot` boundaries — exportable to JSON
and checkable in CI.

## Decision

- **Root `project.cue` is the canonical repo map** — structure, boundaries, and
  `build.*` monorepo project lists (python/node libs, services, suites, report names).
- **`docs/adr/` stays the canonical “why”** — ADR IDs are referenced from CUE (`adr:
  ["004"]`), not duplicated as long prose in `project.cue`.
- **Drift gates:**
  - `make verify-repo-map` — `cue vet` + every `folders` path exists + `build.*`
    matches `make/projects.mk`
  - `make sync-projects-mk` — regenerate `make/projects.mk` lists from `project.cue`
  - **pre-commit** — `verify-repo-map` hook when `project.cue`, `projects.mk`, or
    top-level monorepo paths change (requires `cue` CLI locally)
  - CI runs `make verify-repo-map` on every PR
- **Cursor rule** (`.cursor/rules/05-repo-map.mdc`) — agents read `project.cue` before
  structural work; PRs that add/move top-level paths must update `project.cue`.

## Consequences

- Onboarding and context engineering improve: one machine-readable map for agents.
- Contributors must update `project.cue` when adding top-level folders or changing
  monorepo project membership — CI fails otherwise.
- `make/projects.mk` derived lists can lag if someone edits the file by hand; use
  `make sync-projects-mk` after changing `build.*` in CUE.
- CUE adds a lightweight toolchain dependency (`cue` CLI); verify script uses it in CI
  (install via `setup-go` or pinned binary — see workflow).
- Diagrams, ports, and narrative architecture remain in `docs/architecture.md`; CUE
  does not replace visual docs.
