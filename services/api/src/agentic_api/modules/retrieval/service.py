import logging

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
    def __init__(self, retrieval: AsyncRetrievalReader, settings: ApiSettings) -> None:
        self._retrieval = retrieval
        self._settings = settings

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
        chunks = [ChunkOut.model_validate(c) for c in raw]
        logger.debug(
            "search tenant_id=%s top_k=%s results=%d query_len=%d",
            tenant_id,
            effective_top_k,
            len(chunks),
            len(query),
        )
        return SearchResponse(chunks=chunks)

    async def citation(self, chunk_id: str, *, tenant_id: str) -> CitationOut:
        return CitationOut.model_validate(
            await self._retrieval.get_source_citation(chunk_id, tenant_id=tenant_id)
        )

    async def list_indexed(self, *, tenant_id: str) -> list[IndexedDocumentOut]:
        raw = await self._retrieval.list_indexed_documents(tenant_id=tenant_id)
        return [IndexedDocumentOut.model_validate(d) for d in raw]

    async def document_chunks(self, doc_id: str, *, tenant_id: str) -> DocumentChunksResponse:
        raw = await self._retrieval.list_document_chunks(doc_id, tenant_id=tenant_id)
        chunks = [ChunkOut.model_validate(c) for c in raw]
        source_file = chunks[0].source_file if chunks else None
        return DocumentChunksResponse(doc_id=doc_id, source_file=source_file, chunks=chunks)

    async def source_file_chunks(
        self, source_file: str, *, tenant_id: str
    ) -> DocumentChunksResponse:
        raw = await self._retrieval.list_source_file_chunks(source_file, tenant_id=tenant_id)
        chunks = [ChunkOut.model_validate(c) for c in raw]
        doc_id = chunks[0].doc_id if chunks and chunks[0].doc_id else ""
        return DocumentChunksResponse(
            doc_id=doc_id or source_file, source_file=source_file, chunks=chunks
        )
