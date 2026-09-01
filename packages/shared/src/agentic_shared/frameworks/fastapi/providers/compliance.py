from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentic_shared.core.compliance.noop import NoOpAiTransparency, NoOpAuditLogger
from agentic_shared.core.compliance.protocols import AiTransparencyPort, AuditLogger
from agentic_shared.core.compliance.settings import ComplianceSettings
from agentic_shared.domains.persistence.audit_logger import PostgresAuditLogger
from agentic_shared.infrastructure.sql.core.session import create_session_factory
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings


class ComplianceProvider(Provider):
    """Audit logger + AI system card. Postgres audit only when compliance is enabled."""

    def __init__(
        self,
        compliance: ComplianceSettings,
        database: DatabaseSettings | None = None,
    ) -> None:
        super().__init__()
        self._compliance = compliance
        self._database = database

    @provide(scope=Scope.APP)
    def compliance_settings(self) -> ComplianceSettings:
        return self._compliance

    @provide(scope=Scope.APP)
    def ai_transparency(self) -> AiTransparencyPort:
        return NoOpAiTransparency(self._compliance)

    @provide(scope=Scope.APP)
    def audit_logger(self) -> AuditLogger:
        if (
            not self._compliance.compliance_enabled
            or not self._compliance.audit_log_enabled
            or self._database is None
        ):
            return NoOpAuditLogger()
        factory: async_sessionmaker[AsyncSession] = create_session_factory(
            self._database.database_url
        )
        return PostgresAuditLogger(factory)
