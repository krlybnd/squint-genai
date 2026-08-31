"""Tokenize user/API queries with the same deterministic vault tokens as indexing."""

from __future__ import annotations

import logging

from agentic_shared.domains.pii_vault.extra_recognizers import supplement_analyzer_entities
from agentic_shared.domains.pii_vault.models import TokenCandidate
from agentic_shared.domains.pii_vault.protocols import (
    VaultPersonIdentityPort,
    VaultTokenExistencePort,
)
from agentic_shared.domains.pii_vault.query_spans import expand_adjacent_word_spans
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.domains.pii_vault.tokenizer import PiiTokenizer
from agentic_shared.integrations.litellm.analyzer.protocols import Analyzer

logger = logging.getLogger(__name__)


class QueryPiiTokenizationService:
    def __init__(
        self,
        *,
        analyzer: Analyzer,
        tokenizer: PiiTokenizer,
        settings: PiiVaultSettings,
        existence: VaultTokenExistencePort | None = None,
        person_identity: VaultPersonIdentityPort | None = None,
    ) -> None:
        self._analyzer = analyzer
        self._tokenizer = tokenizer
        self._settings = settings
        self._existence = existence
        self._person_identity = person_identity

    @property
    def enabled(self) -> bool:
        return self._settings.enabled

    async def tokenize_query(self, text: str, *, tenant_id: str) -> str:
        cleaned = text.strip()
        if not self.enabled or not cleaned:
            return cleaned
        if self._existence is None:
            logger.warning(
                "query tokenization skipped: no vault existence port tenant_id=%s",
                tenant_id,
            )
            return cleaned

        entities = await self._analyzer.analyze(cleaned, language=self._settings.language)
        entities = expand_adjacent_word_spans(
            cleaned,
            supplement_analyzer_entities(cleaned, entities),
        )
        candidates = self._tokenizer.iter_candidates(cleaned, entities, tenant_id=tenant_id)
        if not candidates:
            return cleaned

        known = await self._existence.existing_tokens(
            [item.token for item in candidates],
            tenant_id=tenant_id,
        )
        hits = [item for item in candidates if item.token in known]
        hits.extend(await self._identity_hits(cleaned, candidates, known, tenant_id=tenant_id))
        if not hits:
            return cleaned

        replaced = self._tokenizer.apply_vault_hits(cleaned, hits)
        logger.info(
            "query tokenized vault_hits=%d candidates=%d tenant_id=%s",
            len(hits),
            len(candidates),
            tenant_id,
        )
        return replaced

    async def _identity_hits(
        self,
        text: str,
        candidates: list[TokenCandidate],
        known: frozenset[str],
        *,
        tenant_id: str,
    ) -> list[TokenCandidate]:
        if self._person_identity is None:
            return []
        extras: list[TokenCandidate] = []
        seen_spans: set[tuple[int, int]] = set()
        for item in candidates:
            if item.entity_type != "PERSON" or item.token in known:
                continue
            span = (item.start, item.end)
            if span in seen_spans:
                continue
            seen_spans.add(span)
            token = await self._person_identity.token_for_equivalent_name(
                text[item.start : item.end],
                tenant_id=tenant_id,
            )
            if token is None:
                continue
            extras.append(
                TokenCandidate(
                    start=item.start,
                    end=item.end,
                    token=token,
                    entity_type=item.entity_type,
                )
            )
        return extras


__all__ = ["QueryPiiTokenizationService"]
