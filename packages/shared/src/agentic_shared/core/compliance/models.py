from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from agentic_shared.core.compliance.enums import (
    AiRiskTier,
    AuditEventCategory,
    DataSubjectRequestType,
    IncidentSeverity,
)


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Structured audit record for security and privacy accountability."""

    category: AuditEventCategory
    action: str
    actor_id: str | None = None
    tenant_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    outcome: str = "success"
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class DataSubjectRequest:
    """Inbound GDPR data-subject request (to be fulfilled by domain handlers)."""

    request_type: DataSubjectRequestType
    subject_id: str
    tenant_id: str
    request_id: UUID = field(default_factory=uuid4)
    requested_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class IncidentReport:
    """Security incident report hook (NIS2 early-warning workflow)."""

    title: str
    severity: IncidentSeverity
    description: str
    tenant_id: str | None = None
    reporter_id: str | None = None
    incident_id: UUID = field(default_factory=uuid4)
    reported_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AiSystemRecord:
    """EU AI Act transparency metadata for a deployed AI component."""

    system_name: str
    purpose: str
    risk_tier: AiRiskTier
    model_id: str
    provider: str
    human_oversight: bool = True
    logging_enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
