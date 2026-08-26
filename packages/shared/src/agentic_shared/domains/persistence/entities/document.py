from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agentic_shared.domains.persistence.entities.base import (
    AuditMixin,
    TenantScopedEntity,
)

if TYPE_CHECKING:
    from agentic_shared.domains.persistence.entities.index_job import IndexJob


class Document(AuditMixin, TenantScopedEntity):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    minio_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    jobs: Mapped[list[IndexJob]] = relationship(back_populates="document")
