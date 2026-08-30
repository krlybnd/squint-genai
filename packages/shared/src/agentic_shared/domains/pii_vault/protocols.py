from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable
from uuid import UUID

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.domains.pii_vault.models import PiiVaultEntryDraft


@runtime_checkable
class PiiVaultWriteRepositorySync(Protocol):
    def upsert_entries(self, entries: Sequence[PiiVaultEntryDraft]) -> None: ...


@runtime_checkable
class PiiVaultReadRepository(Protocol):
    async def resolve_tokens(self, tokens: Sequence[str]) -> dict[str, SecuredStr]: ...


@runtime_checkable
class QueryPiiTokenizationPort(Protocol):
    @property
    def enabled(self) -> bool: ...

    async def tokenize_query(self, text: str, *, tenant_id: str) -> str: ...


@runtime_checkable
class IndexTimePiiTokenizationPort(Protocol):
    def tokenize_and_store(
        self,
        text: str,
        *,
        doc_id: UUID,
        tenant_id: str,
    ) -> str: ...

    def close(self) -> None: ...


__all__ = [
    "IndexTimePiiTokenizationPort",
    "PiiVaultReadRepository",
    "PiiVaultWriteRepositorySync",
    "QueryPiiTokenizationPort",
]
