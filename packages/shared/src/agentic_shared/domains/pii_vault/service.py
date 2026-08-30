"""Index-time analyze → tokenize → vault persist."""

from __future__ import annotations

import logging
from dataclasses import replace
from uuid import UUID

from agentic_shared.domains.pii_vault.extra_recognizers import supplement_analyzer_entities
from agentic_shared.domains.pii_vault.protocols import PiiVaultWriteRepositorySync
from agentic_shared.domains.pii_vault.tokenizer import PiiTokenizer
from agentic_shared.integrations.litellm.analyzer.sync_client import AnalyzerSyncClient

logger = logging.getLogger(__name__)


class IndexTimePiiService:
    def __init__(
        self,
        *,
        analyzer: AnalyzerSyncClient,
        vault: PiiVaultWriteRepositorySync,
        tokenizer: PiiTokenizer,
        language: str = "en",
    ) -> None:
        self._analyzer = analyzer
        self._vault = vault
        self._tokenizer = tokenizer
        self._language = language

    def tokenize_and_store(
        self,
        text: str,
        *,
        doc_id: UUID,
        tenant_id: str,
    ) -> str:
        entities = self._analyzer.analyze(text, language=self._language)
        entities = supplement_analyzer_entities(text, entities)
        result = self._tokenizer.tokenize(text, entities, tenant_id=tenant_id)
        if result.entries:
            entries = [replace(entry, first_doc_id=doc_id) for entry in result.entries]
            self._vault.upsert_entries(entries)
        logger.info(
            "pii tokenized doc_id=%s entities=%d unique_tokens=%d tenant_id=%s",
            doc_id,
            result.entity_count,
            result.unique_token_count,
            tenant_id,
        )
        return result.text

    def close(self) -> None:
        self._analyzer.close()


__all__ = ["IndexTimePiiService"]
