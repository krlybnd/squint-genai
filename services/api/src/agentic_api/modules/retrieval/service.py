import logging

from agentic_shared.domains.pii_vault.reveal_service import VaultRevealService
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader

from agentic_api.modules.retrieval.schemas import (
    ChunkOut,
    CitationOut,
    DocumentChunksResponse,
    IndexedDocumentOut,
    SearchResponse,
)
from agentic_api.modules.retrieval.settings import get_module_settings
from agentic_api.settings import ApiSettings

logger = logging.getLogger(__name__)


class RetrievalApiService:
    def __init__(
        self,
        retrieval: AsyncRetrievalReader,
        settings: ApiSettings,
        *,
        vault_reveal: VaultRevealService | None = None,
        pii_vault: PiiVaultSettings | None = None,
    ) -> None:
        self._retrieval = retrieval
        self._settings = settings
        self._vault_reveal = vault_reveal
        self._pii_vault = pii_vault

    def _reveal_enabled(self) -> bool:
        return (
            self._vault_reveal is not None
            and self._pii_vault is not None
            and self._pii_vault.enabled
            and self._pii_vault.sse_detokenize_enabled
        )

    async def _reveal_text(self, text: str) -> str:
        if not text or not self._reveal_enabled() or self._vault_reveal is None:
            return text
        return await self._vault_reveal.reveal_text(text, marked=True)

    async def _reveal_chunks(self, chunks: list[ChunkOut]) -> list[ChunkOut]:
        if not self._reveal_enabled():
            return chunks
        revealed: list[ChunkOut] = []
        for chunk in chunks:
            text = await self._reveal_text(chunk.text)
            revealed.append(chunk.model_copy(update={"text": text}))
        return revealed

    async def search(self, query: str, top_k: int | None, *, tenant_id: str) -> SearchResponse:
        module = get_module_settings()
        effective_top_k = top_k
        if effective_top_k is None:
            effective_top_k = module.default_top_k
        if effective_top_k is None:
            effective_top_k = self._settings.qdrant.top_k
        raw = await self._retrieval.search_documents(
            query,
            top_k=effective_top_k,
            tenant_id=tenant_id,
        )
        chunks = await self._reveal_chunks([ChunkOut.model_validate(c) for c in raw])
        logger.debug(
            "search tenant_id=%s top_k=%s results=%d query_len=%d",
            tenant_id,
            effective_top_k,
            len(chunks),
            len(query),
        )
        return SearchResponse(chunks=chunks)

    async def citation(self, chunk_id: str, *, tenant_id: str) -> CitationOut:
        citation = CitationOut.model_validate(
            await self._retrieval.get_source_citation(chunk_id, tenant_id=tenant_id)
        )
        if not self._reveal_enabled():
            return citation
        text = await self._reveal_text(citation.text or "")
        excerpt = await self._reveal_text(citation.excerpt or "")
        return citation.model_copy(update={"text": text or None, "excerpt": excerpt or None})

    async def list_indexed(self, *, tenant_id: str) -> list[IndexedDocumentOut]:
        raw = await self._retrieval.list_indexed_documents(tenant_id=tenant_id)
        return [IndexedDocumentOut.model_validate(d) for d in raw]

    async def document_chunks(self, doc_id: str, *, tenant_id: str) -> DocumentChunksResponse:
        raw = await self._retrieval.list_document_chunks(doc_id, tenant_id=tenant_id)
        chunks = await self._reveal_chunks([ChunkOut.model_validate(c) for c in raw])
        source_file = chunks[0].source_file if chunks else None
        return DocumentChunksResponse(doc_id=doc_id, source_file=source_file, chunks=chunks)

    async def source_file_chunks(
        self, source_file: str, *, tenant_id: str
    ) -> DocumentChunksResponse:
        raw = await self._retrieval.list_source_file_chunks(source_file, tenant_id=tenant_id)
        chunks = await self._reveal_chunks([ChunkOut.model_validate(c) for c in raw])
        doc_id = chunks[0].doc_id if chunks and chunks[0].doc_id else ""
        return DocumentChunksResponse(
            doc_id=doc_id or source_file, source_file=source_file, chunks=chunks
        )
