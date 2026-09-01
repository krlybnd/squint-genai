import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentic_shared.core.compliance.models import AuditEvent
from agentic_shared.core.compliance.protocols import AuditLogger
from agentic_shared.domains.persistence.entities.audit_event import AuditEventRow

logger = logging.getLogger(__name__)


class PostgresAuditLogger:
    """APP-scoped append-only writer; uses its own session (not tenant-bound)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def record(self, event: AuditEvent) -> None:
        row = AuditEventRow(
            id=event.event_id,
            category=event.category.value,
            action=event.action,
            actor_id=event.actor_id,
            tenant_id=event.tenant_id,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            outcome=event.outcome,
            event_metadata=dict(event.metadata),
            occurred_at=event.occurred_at,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()


async def emit_audit(audit: AuditLogger, event: AuditEvent) -> None:
    """Best-effort record; never fail the business request."""
    try:
        await audit.record(event)
    except Exception:
        logger.exception("audit.record failed action=%s", event.action)
