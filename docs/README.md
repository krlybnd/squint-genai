# Documentation

Entry point for **Squint** docs. Start here if you are reviewing the repo or onboarding.

## Recommended reading order

1. **[Project overview](project-overview.md)** — what the system does, who it is for, design principles
2. **[Architecture](architecture.md)** — C4-style Mermaid diagrams (context, containers, agent graph, indexing flow), ports, chunking defaults
3. **[Compliance readiness](compliance.md)** — GDPR / NIS2 / EU AI Act extension points (preparation layer, not certification)
4. **ADRs** — recorded decisions:
   - [001 — Retrieval domain boundary](adr/001-why-mcp-boundary.md)
   - [002 — Service and module settings](adr/002-service-and-module-settings.md)
   - [003 — Compliance extension points](adr/003-compliance-extension-points.md)
   - [004 — No in-service Python integration tests](adr/004-no-in-service-integration-tests.md)
   - [005 — Shared UI core and AppShell](adr/005-shared-ui-core-appshell.md)
   - [006 — Backend i18n for server-emitted copy](adr/006-backend-i18n.md)
   - [007 — No live-stack tests in default CI](adr/007-no-live-tests-in-ci.md)
   - [008 — Repo metadata in CUE (`project.cue`)](adr/008-repo-metadata-in-cue.md)
   - [009 — Soft multi-tenancy in Phase 1 auth](adr/009-soft-tenancy-auth.md)
   - [010 — PoC workflow under `pocs/`](adr/010-poc-workflow.md)

## Quick links

| Topic | Document |
|-------|----------|
| Run locally | Root [README](../README.md) — `make up-ui`, `make up-auth` |
| System diagram | [architecture.md](architecture.md) — L2 container diagram |
| Chat agent nodes | [architecture.md § L3a](architecture.md#l3a--chat-agent-graph) |
| Indexing pipeline | [architecture.md § L3b](architecture.md#l3b--document-indexing-flow) |
| Sample PDFs for demo | [resources/README.md](../resources/README.md) |
| Eval goldens | [tests/eval/dataset.json](../tests/eval/dataset.json) |
| Ops / infra configs | [operations/README.md](../operations/README.md) |
| Repo map (machine-readable) | [project.cue](../project.cue) — `make verify-repo-map` |

## Docs map

```
docs/
  README.md              ← you are here
  project-overview.md    why + capabilities + principles
  architecture.md        diagrams + ports + technical defaults
  compliance.md          regulatory hooks
  adr/                   architecture decision records
```
