from typing import Protocol, runtime_checkable

from agentic_shared.core.compliance.models import (
    AiSystemRecord,
    AuditEvent,
    DataSubjectRequest,
    IncidentReport,
)


@runtime_checkable
class AuditLogger(Protocol):
    """Append-only security / privacy audit trail (NIS2, GDPR accountability)."""

    async def record(self, event: AuditEvent) -> None: ...


@runtime_checkable
class DataSubjectRightsPort(Protocol):
    """GDPR data-subject rights orchestration (access, erasure, portability, …)."""

    async def submit(self, request: DataSubjectRequest) -> str: ...

    async def status(self, request_id: str) -> str: ...


@runtime_checkable
class IncidentReporter(Protocol):
    """NIS2-aligned incident reporting hook (no SIEM required at this layer)."""

    async def report(self, incident: IncidentReport) -> str: ...


@runtime_checkable
class AiTransparencyPort(Protocol):
    """EU AI Act transparency — expose system card / logging policy."""

    def system_record(self) -> AiSystemRecord: ...

    async def log_interaction(
        self,
        *,
        session_id: str,
        tenant_id: str,
        prompt_hash: str,
        outcome: str,
    ) -> None: ...
