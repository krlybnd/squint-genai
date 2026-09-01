from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from agentic_shared.core.settings.secrets import SecuredStr


@dataclass(frozen=True, slots=True)
class PiiVaultEntryDraft:
    """In-memory vault row before Fernet encryption and SQL insert."""

    token: str
    entity_type: str
    plaintext: SecuredStr
    first_doc_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class TokenizedText:
    text: str
    entries: tuple[PiiVaultEntryDraft, ...]
    entity_count: int
    unique_token_count: int


@dataclass(frozen=True, slots=True)
class TokenizeStats:
    entity_count: int
    unique_token_count: int


@dataclass(frozen=True, slots=True)
class TokenCandidate:
    """One query-time span → deterministic token, before vault existence filter."""

    start: int
    end: int
    token: str
    entity_type: str


__all__ = ["PiiVaultEntryDraft", "TokenCandidate", "TokenizeStats", "TokenizedText"]
