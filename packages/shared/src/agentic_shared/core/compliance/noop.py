from agentic_shared.core.compliance.models import (
    AiSystemRecord,
    AuditEvent,
    DataSubjectRequest,
    IncidentReport,
)
from agentic_shared.core.compliance.protocols import (
    AiTransparencyPort,
    AuditLogger,
    DataSubjectRightsPort,
    IncidentReporter,
)
from agentic_shared.core.compliance.settings import ComplianceSettings


class NoOpAuditLogger:
    async def record(self, event: AuditEvent) -> None:
        return None


class NoOpDataSubjectRights:
    async def submit(self, request: DataSubjectRequest) -> str:
        return str(request.request_id)

    async def status(self, request_id: str) -> str:
        return "not_implemented"


class NoOpIncidentReporter:
    async def report(self, incident: IncidentReport) -> str:
        return str(incident.incident_id)


class NoOpAiTransparency:
    def __init__(self, settings: ComplianceSettings | None = None) -> None:
        self._settings = settings or ComplianceSettings()

    def system_record(self) -> AiSystemRecord:
        from agentic_shared.core.compliance.enums import AiRiskTier

        tier = AiRiskTier(self._settings.ai_risk_tier)
        return AiSystemRecord(
            system_name=self._settings.ai_system_name,
            purpose="Document-grounded question answering with retrieval-augmented generation",
            risk_tier=tier,
            model_id="configured-via-litellm",
            provider="litellm-proxy",
            human_oversight=self._settings.ai_human_oversight,
            logging_enabled=self._settings.ai_transparency_enabled,
        )

    async def log_interaction(
        self,
        *,
        session_id: str,
        tenant_id: str,
        prompt_hash: str,
        outcome: str,
    ) -> None:
        return None


def default_compliance_ports() -> tuple[
    AuditLogger,
    DataSubjectRightsPort,
    IncidentReporter,
    AiTransparencyPort,
]:
    settings = ComplianceSettings()
    return (
        NoOpAuditLogger(),
        NoOpDataSubjectRights(),
        NoOpIncidentReporter(),
        NoOpAiTransparency(settings),
    )
