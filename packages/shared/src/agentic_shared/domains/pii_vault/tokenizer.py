"""Deterministic PII span → typed token replacement."""

from __future__ import annotations

import hashlib
import hmac
import re
from collections.abc import Sequence

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.domains.pii_vault.models import (
    PiiVaultEntryDraft,
    TokenCandidate,
    TokenizedText,
)
from agentic_shared.integrations.litellm.analyzer.models import AnalyzerEntity

_TOKEN_PATTERN = re.compile(r"^[A-Z0-9_]+$")


def _normalize_entity_type(entity_type: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", entity_type.strip().upper())
    return cleaned or "ENTITY"


def make_deterministic_token(
    entity_type: str,
    value: str,
    *,
    tenant_id: str,
    token_salt: str,
) -> str:
    """Return `<ENTITYTYPE_hash8>` stable per tenant + type + normalized value."""
    normalized_type = _normalize_entity_type(entity_type)
    normalized_value = value.strip().casefold()
    digest_input = f"{tenant_id}|{normalized_type}|{normalized_value}".encode()
    digest = (
        hmac.new(token_salt.encode("utf-8"), digest_input, hashlib.sha256).hexdigest()[:8].upper()
    )
    token_body = f"{normalized_type}_{digest}"
    if not _TOKEN_PATTERN.match(token_body):
        token_body = f"ENTITY_{digest}"
    return f"<{token_body}>"


def _select_non_overlapping(entities: Sequence[AnalyzerEntity]) -> list[AnalyzerEntity]:
    """Greedy left-to-right: keep higher-score span when ranges overlap."""
    ordered = sorted(entities, key=lambda e: (e.start, -(e.end - e.start), -e.score))
    kept: list[AnalyzerEntity] = []
    for entity in ordered:
        if entity.start < 0 or entity.end <= entity.start:
            continue
        if kept and entity.start < kept[-1].end:
            previous = kept[-1]
            previous_len = previous.end - previous.start
            current_len = entity.end - entity.start
            if entity.score > previous.score or (
                entity.score == previous.score and current_len > previous_len
            ):
                kept[-1] = entity
            continue
        kept.append(entity)
    return kept


class PiiTokenizer:
    def __init__(self, *, token_salt: str) -> None:
        self._token_salt = token_salt

    def tokenize(
        self,
        text: str,
        entities: Sequence[AnalyzerEntity],
        *,
        tenant_id: str,
    ) -> TokenizedText:
        if not entities:
            return TokenizedText(text=text, entries=(), entity_count=0, unique_token_count=0)

        selected = _select_non_overlapping(entities)
        token_by_span: dict[tuple[int, int], str] = {}
        unique_entries: dict[str, PiiVaultEntryDraft] = {}

        for entity in selected:
            if entity.end > len(text):
                continue
            value = text[entity.start : entity.end]
            if not value.strip():
                continue
            token = make_deterministic_token(
                entity.entity_type,
                value,
                tenant_id=tenant_id,
                token_salt=self._token_salt,
            )
            token_by_span[(entity.start, entity.end)] = token
            if token not in unique_entries:
                unique_entries[token] = PiiVaultEntryDraft(
                    token=token,
                    entity_type=_normalize_entity_type(entity.entity_type),
                    plaintext=SecuredStr(value),
                )

        parts: list[str] = []
        cursor = 0
        for start, end in sorted(token_by_span):
            parts.append(text[cursor:start])
            parts.append(token_by_span[(start, end)])
            cursor = end
        parts.append(text[cursor:])
        tokenized = "".join(parts)

        entries = tuple(unique_entries.values())
        return TokenizedText(
            text=tokenized,
            entries=entries,
            entity_count=len(selected),
            unique_token_count=len(entries),
        )

    def iter_candidates(
        self,
        text: str,
        entities: Sequence[AnalyzerEntity],
        *,
        tenant_id: str,
    ) -> list[TokenCandidate]:
        """Hash every valid span (no overlap filter) for a vault existence check."""
        candidates: list[TokenCandidate] = []
        seen: set[tuple[int, int, str]] = set()
        for entity in entities:
            if entity.start < 0 or entity.end <= entity.start or entity.end > len(text):
                continue
            value = text[entity.start : entity.end]
            if not value.strip():
                continue
            token = make_deterministic_token(
                entity.entity_type,
                value,
                tenant_id=tenant_id,
                token_salt=self._token_salt,
            )
            key = (entity.start, entity.end, token)
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                TokenCandidate(
                    start=entity.start,
                    end=entity.end,
                    token=token,
                    entity_type=_normalize_entity_type(entity.entity_type),
                )
            )
        return candidates

    def apply_vault_hits(self, text: str, hits: Sequence[TokenCandidate]) -> str:
        """Replace longest non-overlapping vault-confirmed spans."""
        if not hits:
            return text
        entities = [
            AnalyzerEntity(
                entity_type=hit.entity_type,
                start=hit.start,
                end=hit.end,
                score=float(hit.end - hit.start),
            )
            for hit in hits
        ]
        token_by_span = {(hit.start, hit.end): hit.token for hit in hits}
        parts: list[str] = []
        cursor = 0
        for entity in _select_non_overlapping(entities):
            token = token_by_span.get((entity.start, entity.end))
            if token is None:
                continue
            parts.append(text[cursor : entity.start])
            parts.append(token)
            cursor = entity.end
        parts.append(text[cursor:])
        return "".join(parts)


__all__ = ["PiiTokenizer", "make_deterministic_token"]
