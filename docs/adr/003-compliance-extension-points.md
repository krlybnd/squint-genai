# ADR 003: Compliance extension points

## Context

Operators deploying agentic-rag-eval in the EU may need to demonstrate readiness for
GDPR (personal data), NIS2 (security logging and incidents), and the EU AI Act
(transparency and logging for AI systems). Bundling SIEM tools (Wazuh, Elastic) is out
of scope; the backend should expose **ports** that deployments can wire to their own
storage and processes.

## Decision

Add `agentic_shared/core/compliance/` with:

- **Protocols:** `AuditLogger`, `DataSubjectRightsPort`, `IncidentReporter`, `AiTransparencyPort`
- **Models:** `AuditEvent`, `DataSubjectRequest`, `IncidentReport`, `AiSystemRecord`
- **Settings:** `ComplianceSettings` (retention days, AI metadata, toggles)
- **NoOp defaults** for development until services inject real adapters

Existing PII redaction (`core/security/guard/`) and auth (`crosscut/auth/`) remain separate;
compliance layer records events and orchestrates rights requests, not duplicate guard logic.

Documentation: `docs/compliance.md`, `docs/project-overview.md`.

## Consequences

- Services can adopt compliance incrementally via Dishka providers
- No breaking change — all ports default to NoOp
- Full GDPR erasure/export and audit persistence are roadmap items, not Phase 1 blockers
