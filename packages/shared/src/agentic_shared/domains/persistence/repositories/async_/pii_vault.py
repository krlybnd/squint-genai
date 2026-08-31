from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.crosscut.crypto.cipher import Cipher
from agentic_shared.domains.persistence.entities.pii_vault import PiiVaultEntry
from agentic_shared.infrastructure.sql.core.repository import SqlAlchemyReadRepository


class SqlAlchemyPiiVaultReadRepository(SqlAlchemyReadRepository[PiiVaultEntry]):
    def __init__(self, session: AsyncSession, tenant_id: str, cipher: Cipher) -> None:
        super().__init__(session, PiiVaultEntry, tenant_id)
        self._cipher = cipher

    async def resolve_tokens(self, tokens: Sequence[str]) -> dict[str, SecuredStr]:
        unique = sorted({token for token in tokens if token})
        if not unique:
            return {}
        result = await self._session.execute(
            select(PiiVaultEntry).where(
                PiiVaultEntry.tenant_id == self._tenant_id,
                PiiVaultEntry.token.in_(unique),
            )
        )
        resolved: dict[str, SecuredStr] = {}
        for entry in result.scalars().all():
            resolved[entry.token] = self._cipher.decrypt(entry.ciphertext)
        return resolved

    async def existing_tokens(self, tokens: Sequence[str]) -> frozenset[str]:
        unique = sorted({token for token in tokens if token})
        if not unique:
            return frozenset()
        result = await self._session.execute(
            select(PiiVaultEntry.token).where(
                PiiVaultEntry.tenant_id == self._tenant_id,
                PiiVaultEntry.token.in_(unique),
            )
        )
        return frozenset(result.scalars().all())


__all__ = ["SqlAlchemyPiiVaultReadRepository"]
