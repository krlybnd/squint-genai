from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from agentic_shared.domains.persistence.entities.base import (
    AuditMixin,
    TenantScopedEntity,
)


class ChatSession(AuditMixin, TenantScopedEntity):
    __tablename__ = "chat_sessions"

    title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    messages: Mapped[list[ChatMessage]] = relationship(back_populates="session")


class ChatMessage(AuditMixin, TenantScopedEntity):
    __tablename__ = "chat_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    session: Mapped[ChatSession] = relationship(back_populates="messages")
