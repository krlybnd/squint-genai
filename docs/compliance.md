# Compliance readiness (GDPR, NIS2, EU AI Act)

This document describes how **Squint** prepares for European regulatory requirements. The backend includes **extension points** in `packages/shared/src/agentic_shared/core/compliance/` — not a certified compliance product and **no external SIEM** (e.g. Wazuh) is bundled.

> **Status:** preparation layer — protocols, models, settings, and NoOp defaults. Domain handlers and persistence for audit logs are **roadmap items**.

## Regulatory scope (high level)

| Framework | Relevance to this system | Current backend support |
|-----------|-------------------------|-------------------------|
| **GDPR** | User documents, chat messages, auth identities, LLM provider subprocessors | PII redaction, tenant scoping, data-subject request ports, retention settings |
| **NIS2** | Operator of essential/important digital services using this stack | Structured audit events, incident report port, auth/RBAC |
| **EU AI Act** | Deployed RAG/chat as AI system assisting users | Transparency record, interaction logging port, human-oversight flag, risk tier setting |

Legal interpretation and organizational policies remain the **operator's responsibility**. This codebase provides technical hooks and documentation.

---

## Shared compliance layer

Location: `agentic_shared/core/compliance/`

```
compliance/
  enums.py       AuditEventCategory, DataSubjectRequestType, IncidentSeverity, AiRiskTier
  models.py      AuditEvent, DataSubjectRequest, IncidentReport, AiSystemRecord
  protocols.py   AuditLogger, DataSubjectRightsPort, IncidentReporter, AiTransparencyPort
  settings.py    ComplianceSettings (retention, toggles, AI metadata)
  noop.py        NoOp* implementations for dev / until wired
```

### Design rules

1. **Ports, not vendors** — log to Postgres, stdout, or an external API via future adapters; no Wazuh/Elastic bundled.
2. **Opt-in** — `ComplianceSettings.compliance_enabled` defaults to `false`; services inject ports when ready.
3. **Reuse existing security** — PII redaction stays in `core/security/guard/`; compliance layer records *that* redaction occurred, not duplicate logic.
4. **Tenant-aware** — all models carry optional `tenant_id` for multi-tenant erasure/export.

---

## GDPR

### Already in the codebase

| Requirement area | Implementation |
|------------------|----------------|
| Data minimization (Art. 5) | PII redaction before LLM provider (`core/security/guard/pii.py`); guard node in chat |
| Purpose limitation | RAG scoped to uploaded/indexed documents; system prompts in module settings |
| Storage limitation | `ComplianceSettings.document_retention_days`, `chat_retention_days` (enforcement TBD) |
| Integrity & confidentiality | TLS at edge (Traefik), auth (Keycloak/API key), RBAC |
| Accountability | `AuditEvent` + `AuditLogger` protocol; entity `AuditMixin` (`created_at`, `updated_at`) |
| Tenant isolation | `tenant_id` on persisted entities; resolved from auth context |

### Prepared hooks (not yet wired)

| Right (Art.) | Port | Planned handler |
|--------------|------|-----------------|
| Access (15) | `DataSubjectRightsPort.submit(ACCESS)` | Export chat sessions + document metadata for subject |
| Erasure (17) | `DataSubjectRightsPort.submit(ERASURE)` | Delete MinIO object, Qdrant vectors, Postgres rows |
| Portability (20) | `DataSubjectRightsPort.submit(PORTABILITY)` | JSON export of user chat + document list |
| Restriction (18) | `DataSubjectRightsPort.submit(RESTRICTION)` | Flag tenant/user; block new indexing |

### Roadmap

- [ ] `POST /v1/privacy/requests` API module (api service)
- [ ] Celery task: `erase_tenant_data`, `export_subject_data`
- [ ] Postgres `audit_events` table + `PostgresAuditLogger`
- [ ] Retention cron: purge documents/chats past `*_retention_days`
- [ ] DPIA template in `docs/compliance/dpia-template.md`
- [ ] Record of Processing Activities (ROPA) template

### Environment variables (`ComplianceSettings`)

```env
COMPLIANCE_ENABLED=false
DOCUMENT_RETENTION_DAYS=365
CHAT_RETENTION_DAYS=90
AUDIT_RETENTION_DAYS=730
AUDIT_LOG_ENABLED=true
```

---

## NIS2

NIS2 emphasizes risk management, incident handling, and logging for operators of critical services. This repo does **not** replace an ISMS; it offers **structured hooks**.

### Prepared hooks

| NIS2 theme | Backend hook |
|------------|--------------|
| Access control | Keycloak JWT, `AppRole`, `require_roles()` on routes |
| Logging & monitoring | `AuditLogger.record(AuditEvent)` with categories: `auth`, `access`, `data_change`, `incident` |
| Incident handling | `IncidentReporter.report(IncidentReport)` with `IncidentSeverity` |
| Supply chain | SBOM export + license gate via `make licenses` (CycloneDX merge + [Grant](https://github.com/anchore/grant) policy in `.grant.yaml`); LiteLLM as configurable LLM gateway |

### Roadmap

- [ ] `PostgresAuditLogger` — append-only audit table
- [ ] Admin endpoint or internal tool to list/open incidents
- [ ] Runbook doc: `docs/compliance/incident-response.md`
- [ ] Security contact + notification SLA documented per deployment

---

## EU AI Act

This system is likely **limited risk** (transparency obligations) when deployed as a document Q&A assistant — final classification depends on use case and deployer.

### Prepared hooks

| Obligation area | Backend hook |
|-----------------|--------------|
| Transparency | `AiTransparencyPort.system_record()` → `AiSystemRecord` (name, purpose, model, risk tier) |
| Logging | `AiTransparencyPort.log_interaction(session_id, tenant_id, prompt_hash, outcome)` |
| Human oversight | `ComplianceSettings.ai_human_oversight`; guard node blocks harmful input |
| Technical documentation | This doc + [project-overview.md](project-overview.md) + ADRs |

### Roadmap

- [ ] `GET /v1/ai/system-card` — public transparency JSON from `AiSystemRecord`
- [ ] Persist interaction logs (hashed prompts, retrieval chunk IDs, model version)
- [ ] Conformity assessment checklist for high-risk deployments (if applicable)
- [ ] Eval pipeline as evidence for accuracy / robustness testing

### Environment variables

```env
AI_TRANSPARENCY_ENABLED=true
AI_SYSTEM_NAME=agentic-rag-eval
AI_RISK_TIER=limited
AI_HUMAN_OVERSIGHT=true
```

---

## Wiring guide (for implementers)

When ready to enable compliance in a service:

```python
from agentic_shared.core.compliance import (
    AuditEvent,
    AuditEventCategory,
    ComplianceSettings,
    NoOpAuditLogger,
)

settings = ComplianceSettings()
audit: AuditLogger = NoOpAuditLogger()  # replace with PostgresAuditLogger

await audit.record(
    AuditEvent(
        category=AuditEventCategory.AI_INTERACTION,
        action="chat.stream.completed",
        tenant_id=tenant_id,
        actor_id=user_id,
        resource_type="chat_session",
        resource_id=str(session_id),
    )
)
```

Replace NoOp adapters in Dishka providers per service — same pattern as `DatabaseProvider(settings.database)`.

---

## Related code (outside `core/compliance`)

| Path | Role |
|------|------|
| `core/security/guard/pii.py` | GDPR — personal data redaction before LLM |
| `core/security/guard/injection.py` | Security — prompt injection detection |
| `crosscut/auth/` | Access control, tenant resolution |
| `domains/persistence/entities/base.py` | `AuditMixin`, `TenantMixin` |
| `services/chat/core/guard/` | Agent guard node (PII + injection rules) |
| `tests/eval/` | DeepEval generation gate + Pydantic Evals retrieval IR + golden dataset (AI quality evidence) |
| Chat + `LANGSMITH_*` | Production LangGraph trace export for monitoring |

---

## Disclaimer

This software is a **reference implementation**. Compliance with GDPR, NIS2, and the EU AI Act requires legal review, organizational processes, and deployment-specific controls. The hooks described here reduce integration cost but do **not** constitute legal advice or certification.
