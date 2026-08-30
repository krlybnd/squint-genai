---
name: poc
description: >-
  Create and run Squint PoCs under pocs/ (ADR 010): mandatory poc.md from the j2
  template, thin scripts/poc.sh that tees a light results/result.log (gitignored).
  Use when scaffolding or running a PoC, or writing PoC findings.
---

# PoC workflow (ADR 010)

## Rules

1. New PoC → `pocs/<snake_name>/`.
2. **`poc.md` is mandatory** — copy/fill from `templates/poc.md.j2` (AI or human).
3. Copy **`scripts/poc.sh.skeleton`** → `scripts/poc.sh`; implement the TODO blocks only.
   Optional: `check.sh.skeleton` → `check.sh` (alias to `poc.sh`) — only if you want that name.
4. Run `./scripts/poc.sh` → tees **`results/result.log`** (gitignored). Log = proof.
5. Read the log → fill **Interpretation** + **Decision** in `poc.md`.
6. Update `project.cue`; `make verify-repo-map`.
7. No shared lib. No rigid result schema — keep the script short and chatty.

## Layout

```
pocs/<name>/
  poc.md              # required (from j2)
  scripts/poc.sh      # from skeleton
  compose.yaml        # if needed
  run/                # gitignored
  results/            # gitignored (result.log)
```
