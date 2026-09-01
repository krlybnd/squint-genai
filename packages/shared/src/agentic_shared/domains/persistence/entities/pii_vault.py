from __future__ import annotations

import uuid

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from agentic_shared.domains.persistence.entities.base import AuditMixin, TenantScopedEntity


class PiiVaultEntry(AuditMixin, TenantScopedEntity):
    """Encrypted token → plaintext mapping for index-time PII tokenization."""

    __tablename__ = "pii_vault_entries"
    __table_args__ = (UniqueConstraint("tenant_id", "token", name="uq_pii_vault_tenant_token"),)

    token: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    first_doc_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)


__all__ = ["PiiVaultEntry"]
