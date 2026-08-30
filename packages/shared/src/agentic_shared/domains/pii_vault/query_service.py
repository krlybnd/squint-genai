"""Tokenize user/API queries with the same deterministic vault tokens as indexing."""

from __future__ import annotations

import logging

from agentic_shared.domains.pii_vault.extra_recognizers import supplement_analyzer_entities
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
    ) -> None:
        self._analyzer = analyzer
        self._tokenizer = tokenizer
        self._settings = settings

    @property
    def enabled(self) -> bool:
        return self._settings.enabled

    async def tokenize_query(self, text: str, *, tenant_id: str) -> str:
        cleaned = text.strip()
        if not self.enabled or not cleaned:
            return cleaned
        entities = await self._analyzer.analyze(cleaned, language=self._settings.language)
        entities = supplement_analyzer_entities(cleaned, entities)
        result = self._tokenizer.tokenize(cleaned, entities, tenant_id=tenant_id)
        if result.entity_count:
            logger.info(
                "query tokenized entities=%d unique_tokens=%d tenant_id=%s",
                result.entity_count,
                result.unique_token_count,
                tenant_id,
            )
        return result.text


__all__ = ["QueryPiiTokenizationService"]
