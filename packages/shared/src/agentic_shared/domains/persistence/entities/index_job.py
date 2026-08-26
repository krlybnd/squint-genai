from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agentic_shared.domains.persistence.entities.base import (
    AuditMixin,
    TenantScopedEntity,
)

if TYPE_CHECKING:
    from agentic_shared.domains.persistence.entities.document import Document


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IndexJob(AuditMixin, TenantScopedEntity):
    __tablename__ = "index_jobs"

    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(
            JobStatus,
            name="job_status",
            values_callable=lambda statuses: [s.value for s in statuses],
        ),
        default=JobStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    document: Mapped[Document | None] = relationship(back_populates="jobs")
