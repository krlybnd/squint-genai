"""Lookup whether index-time vault tokens exist — no decrypt, no insert."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agentic_shared.crosscut.crypto.cipher import Cipher
from agentic_shared.domains.persistence.entities.pii_vault import PiiVaultEntry
from agentic_shared.domains.pii_vault.name_identity import person_name_key, same_person_name


class SqlAlchemyVaultTokenLookup:
    """APP-scoped ``EXISTS`` on ``(tenant_id, token)`` — unique constraint path."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def existing_tokens(
        self,
        tokens: Sequence[str],
        *,
        tenant_id: str,
    ) -> frozenset[str]:
        unique = sorted({token for token in tokens if token})
        if not unique:
            return frozenset()
        async with self._session_factory() as session:
            result = await session.execute(
                select(PiiVaultEntry.token).where(
                    PiiVaultEntry.tenant_id == tenant_id,
                    PiiVaultEntry.token.in_(unique),
                )
            )
            return frozenset(result.scalars().all())


class SqlAlchemyVaultPersonIdentity:
    """Resolve a query name to the PERSON token stored at index time."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], cipher: Cipher) -> None:
        self._session_factory = session_factory
        self._cipher = cipher

    async def token_for_equivalent_name(self, name: str, *, tenant_id: str) -> str | None:
        query_key = person_name_key(name)
        if len(query_key) < 2:
            return None
        async with self._session_factory() as session:
            result = await session.execute(
                select(PiiVaultEntry.token, PiiVaultEntry.ciphertext).where(
                    PiiVaultEntry.tenant_id == tenant_id,
                    PiiVaultEntry.entity_type == "PERSON",
                )
            )
            rows = result.all()
        for token, ciphertext in rows:
            try:
                plaintext = self._cipher.decrypt(ciphertext).get_secret_value()
            except ValueError:
                continue
            if same_person_name(name, plaintext):
                return str(token)
        return None


__all__ = ["SqlAlchemyVaultPersonIdentity", "SqlAlchemyVaultTokenLookup"]
