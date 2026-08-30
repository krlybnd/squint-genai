from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from agentic_shared.crosscut.crypto.cipher import Cipher
from agentic_shared.domains.persistence.entities.pii_vault import PiiVaultEntry
from agentic_shared.domains.pii_vault.models import PiiVaultEntryDraft


class SqlAlchemyPiiVaultWriteRepositorySync:
    def __init__(self, session: Session, tenant_id: str, cipher: Cipher) -> None:
        self._session = session
        self._tenant_id = tenant_id
        self._cipher = cipher

    def upsert_entries(self, entries: Sequence[PiiVaultEntryDraft]) -> None:
        if not entries:
            return
        rows = [
            {
                "id": uuid.uuid4(),
                "tenant_id": self._tenant_id,
                "token": entry.token,
                "entity_type": entry.entity_type,
                "ciphertext": self._cipher.encrypt(entry.plaintext),
                "first_doc_id": entry.first_doc_id,
            }
            for entry in entries
        ]
        stmt = insert(PiiVaultEntry).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["tenant_id", "token"])
        self._session.execute(stmt)
        self._session.commit()


__all__ = ["SqlAlchemyPiiVaultWriteRepositorySync"]
