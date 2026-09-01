import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from agentic_shared.core.compliance.enums import AuditEventCategory
from agentic_shared.core.compliance.models import AuditEvent
from agentic_shared.core.compliance.noop import NoOpAuditLogger
from agentic_shared.core.compliance.settings import ComplianceSettings
from agentic_shared.domains.persistence.audit_logger import PostgresAuditLogger, emit_audit
from agentic_shared.frameworks.fastapi.providers.compliance import ComplianceProvider
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings


class TestPostgresAuditLogger(unittest.IsolatedAsyncioTestCase):
    async def test_record_commits_mapped_row(self) -> None:
        # Arrange
        session = MagicMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        factory = MagicMock(return_value=session)
        logger = PostgresAuditLogger(factory)
        event = AuditEvent(
            category=AuditEventCategory.AUTH,
            action="http.unauthorized",
            outcome="failure",
            actor_id="u1",
            tenant_id="tenant-a",
        )

        # Act
        await logger.record(event)

        # Assert
        factory.assert_called_once()
        session.add.assert_called_once()
        row = session.add.call_args.args[0]
        self.assertEqual(row.action, "http.unauthorized")
        self.assertEqual(row.category, "auth")
        self.assertEqual(row.actor_id, "u1")
        session.commit.assert_awaited_once()

    async def test_emit_audit_swallows_logger_errors(self) -> None:
        # Arrange
        audit = MagicMock()
        audit.record = AsyncMock(side_effect=RuntimeError("db down"))
        event = AuditEvent(category=AuditEventCategory.AUTH, action="x")

        # Act / Assert
        await emit_audit(audit, event)


class TestComplianceProvider(unittest.TestCase):
    def test_disabled_compliance_uses_noop_audit(self) -> None:
        # Arrange
        provider = ComplianceProvider(
            ComplianceSettings(compliance_enabled=False),
            DatabaseSettings(),
        )

        # Act
        logger = provider.audit_logger()

        # Assert
        self.assertIsInstance(logger, NoOpAuditLogger)

    def test_enabled_without_database_uses_noop(self) -> None:
        # Arrange
        provider = ComplianceProvider(ComplianceSettings(compliance_enabled=True), None)

        # Act
        logger = provider.audit_logger()

        # Assert
        self.assertIsInstance(logger, NoOpAuditLogger)


class TestComplianceProviderPostgres(unittest.TestCase):
    def test_enabled_builds_postgres_logger(self) -> None:
        # Arrange
        provider = ComplianceProvider(
            ComplianceSettings(compliance_enabled=True, audit_log_enabled=True),
            DatabaseSettings(),
        )

        # Act
        with patch(
            "agentic_shared.frameworks.fastapi.providers.compliance.create_session_factory",
            return_value=MagicMock(),
        ):
            logger = provider.audit_logger()

        # Assert
        self.assertIsInstance(logger, PostgresAuditLogger)


if __name__ == "__main__":
    unittest.main()
