import asyncio
import logging
from collections.abc import Callable

from agentic_shared.domains.pii_vault.protocols import QueryPiiTokenizationPort
from agentic_shared.domains.retrieval.models import (
    ChunkPreview,
    IndexedDocumentEntry,
    RetrievedChunk,
    SearchDocumentsResult,
    SearchMeta,
    SourceCitation,
)
from agentic_shared.domains.retrieval.protocols.chunks import ChunkReadRepository
from agentic_shared.infrastructure.vector.core.payload import payload_page, payload_text
from agentic_shared.infrastructure.vector.qdrant.dense import embed_dense_text
from agentic_shared.infrastructure.vector.qdrant.sparse import embed_sparse_text
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings

logger = logging.getLogger(__name__)


class RetrievalService:
    """Hybrid retrieval (dense + sparse RRF)."""

    def __init__(
        self,
        chunk_read: ChunkReadRepository,
        llm: LiteLLMChatSettings,
        embedding: LiteLLMEmbeddingSettings,
        query_pii: QueryPiiTokenizationPort | None = None,
    ) -> None:
        self._chunk_read = chunk_read
        self._llm = llm
        self._embedding = embedding
        self._query_pii = query_pii

    def search_documents(
        self, query: str, top_k: int | None = None, *, tenant_id: str
    ) -> list[RetrievedChunk]:
        return self.search_documents_with_meta(query, top_k=top_k, tenant_id=tenant_id).chunks

    async def search_documents_async(
        self, query: str, top_k: int | None = None, *, tenant_id: str
    ) -> list[RetrievedChunk]:
        result = await self.search_documents_with_meta_async(
            query, top_k=top_k, tenant_id=tenant_id
        )
        return result.chunks

    @staticmethod
    def _attach_chunk_lists(
        meta: SearchMeta,
        candidates: list[RetrievedChunk],
        final_chunks: list[RetrievedChunk],
    ) -> SearchMeta:
        selected_ids = {chunk.chunk_id for chunk in final_chunks}
        return meta.model_copy(
            update={
                "rrf_candidates": [
                    ChunkPreview.from_chunk(
                        chunk,
                        rank=index + 1,
                        selected=chunk.chunk_id in selected_ids,
                    )
                    for index, chunk in enumerate(candidates)
                ],
                "final_chunks": [
                    ChunkPreview.from_chunk(chunk, rank=index + 1, selected=True)
                    for index, chunk in enumerate(final_chunks)
                ],
            }
        )

    def _search_meta(self, query: str, top_k: int | None) -> tuple[str, int, int, SearchMeta]:
        cleaned = query.strip()
        final_k = top_k if top_k is not None else self._chunk_read.default_top_k
        candidate_k = max(final_k, self._chunk_read.candidate_top_k)
        meta = SearchMeta.hybrid_start(
            query=cleaned,
            dense_model=self._embedding.embedding_model,
            sparse_model=self._chunk_read.sparse_model,
            candidate_top_k=candidate_k,
            final_top_k=final_k,
        )
        return cleaned, final_k, candidate_k, meta

    async def _prepare_query_async(self, query: str, *, tenant_id: str) -> str:
        cleaned = query.strip()
        if not cleaned or self._query_pii is None or not self._query_pii.enabled:
            return cleaned
        return await self._query_pii.tokenize_query(cleaned, tenant_id=tenant_id)

    def _prepare_query_sync(self, query: str, *, tenant_id: str) -> str:
        cleaned = query.strip()
        if not cleaned or self._query_pii is None or not self._query_pii.enabled:
            return cleaned
        return asyncio.run(self._query_pii.tokenize_query(cleaned, tenant_id=tenant_id))

    def search_documents_with_meta(
        self, query: str, top_k: int | None = None, *, tenant_id: str
    ) -> SearchDocumentsResult:
        cleaned, final_k, candidate_k, meta = self._search_meta(query, top_k)
        if not cleaned:
            return SearchDocumentsResult(chunks=[], meta=meta)

        cleaned = self._prepare_query_sync(cleaned, tenant_id=tenant_id)
        meta = meta.model_copy(update={"query": cleaned})
        if not cleaned:
            return SearchDocumentsResult(chunks=[], meta=meta)

        try:
            dense_vector = embed_dense_text(cleaned, llm=self._llm, embedding=self._embedding)
            sparse_vector = embed_sparse_text(
                cleaned,
                model_name=self._chunk_read.sparse_model,
            )
        except Exception as exc:
            logger.warning("retrieval embedding failed", exc_info=True)
            return SearchDocumentsResult(chunks=[], meta=meta.with_error(str(exc)))

        raw_candidates = self._chunk_read.hybrid_search(
            tenant_id=tenant_id,
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            limit=candidate_k,
        )
        result = self._rank_candidates(list(raw_candidates), meta=meta, final_k=final_k)
        logger.debug(
            "retrieval search tenant_id=%s candidates=%d results=%d",
            tenant_id,
            result.meta.candidates_found,
            len(result.chunks),
        )
        return result

    async def search_documents_with_meta_async(
        self, query: str, top_k: int | None = None, *, tenant_id: str
    ) -> SearchDocumentsResult:
        cleaned, final_k, candidate_k, meta = self._search_meta(query, top_k)
        if not cleaned:
            return SearchDocumentsResult(chunks=[], meta=meta)

        cleaned = await self._prepare_query_async(cleaned, tenant_id=tenant_id)
        meta = meta.model_copy(update={"query": cleaned})
        if not cleaned:
            return SearchDocumentsResult(chunks=[], meta=meta)

        try:
            dense_vector, sparse_vector = await asyncio.gather(
                asyncio.to_thread(
                    embed_dense_text,
                    cleaned,
                    llm=self._llm,
                    embedding=self._embedding,
                ),
                asyncio.to_thread(
                    embed_sparse_text,
                    cleaned,
                    model_name=self._chunk_read.sparse_model,
                ),
            )
        except Exception as exc:
            logger.warning("retrieval embedding failed", exc_info=True)
            return SearchDocumentsResult(chunks=[], meta=meta.with_error(str(exc)))

        raw_candidates = await asyncio.to_thread(
            self._chunk_read.hybrid_search,
            tenant_id=tenant_id,
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            limit=candidate_k,
        )
        result = self._rank_candidates(list(raw_candidates), meta=meta, final_k=final_k)
        logger.debug(
            "retrieval search tenant_id=%s candidates=%d results=%d",
            tenant_id,
            result.meta.candidates_found,
            len(result.chunks),
        )
        return result

    @staticmethod
    def _rank_candidates(
        candidates: list[RetrievedChunk],
        *,
        meta: SearchMeta,
        final_k: int,
    ) -> SearchDocumentsResult:
        meta = meta.with_candidate_count(len(candidates))
        if not candidates:
            return SearchDocumentsResult(chunks=[], meta=meta)

        final_chunks = candidates[:final_k]
        meta = RetrievalService._attach_chunk_lists(meta, candidates, final_chunks)
        return SearchDocumentsResult(chunks=final_chunks, meta=meta)

    def get_source_citation(self, chunk_id: str, *, tenant_id: str) -> SourceCitation:
        try:
            payload = self._chunk_read.get_by_id(chunk_id, tenant_id=tenant_id)
            if payload is None:
                return SourceCitation(chunk_id=chunk_id, error="not found")
            text = payload_text(payload)
            return SourceCitation(
                chunk_id=chunk_id,
                page=payload_page(payload),
                section=payload.section,
                source_file=payload.source_file,
                doc_id=payload.doc_id,
                text=text,
                excerpt=text[:300],
            )
        except Exception as exc:
            logger.warning("citation lookup failed chunk_id=%s", chunk_id, exc_info=True)
            return SourceCitation(chunk_id=chunk_id, error=str(exc))

    async def get_source_citation_async(self, chunk_id: str, *, tenant_id: str) -> SourceCitation:
        return await asyncio.to_thread(self.get_source_citation, chunk_id, tenant_id=tenant_id)

    def list_document_chunks(
        self, doc_id: str, *, tenant_id: str, limit: int = 500
    ) -> list[RetrievedChunk]:
        return self._scroll_all_chunks(
            lambda batch, offset: self._chunk_read.scroll_document_chunks(
                doc_id, tenant_id=tenant_id, limit=batch, offset=offset
            ),
            limit=limit,
        )

    async def list_document_chunks_async(
        self, doc_id: str, *, tenant_id: str, limit: int = 500
    ) -> list[RetrievedChunk]:
        return await asyncio.to_thread(
            self.list_document_chunks, doc_id, tenant_id=tenant_id, limit=limit
        )

    def list_source_file_chunks(
        self, source_file: str, *, tenant_id: str, limit: int = 500
    ) -> list[RetrievedChunk]:
        return self._scroll_all_chunks(
            lambda batch, offset: self._chunk_read.scroll_source_file_chunks(
                source_file, tenant_id=tenant_id, limit=batch, offset=offset
            ),
            limit=limit,
            dedupe=True,
        )

    async def list_source_file_chunks_async(
        self, source_file: str, *, tenant_id: str, limit: int = 500
    ) -> list[RetrievedChunk]:
        return await asyncio.to_thread(
            self.list_source_file_chunks,
            source_file,
            tenant_id=tenant_id,
            limit=limit,
        )

    def _scroll_all_chunks(
        self,
        scroll_fn: Callable[[int, str | None], tuple[list[RetrievedChunk], str | None]],
        *,
        limit: int,
        dedupe: bool = False,
    ) -> list[RetrievedChunk]:
        all_chunks: list[RetrievedChunk] = []
        offset: str | None = None
        while len(all_chunks) < limit:
            batch, offset = scroll_fn(min(100, limit - len(all_chunks)), offset)
            all_chunks.extend(batch)
            if offset is None or not batch:
                break

        if dedupe:
            seen: set[str] = set()
            unique: list[RetrievedChunk] = []
            for chunk in all_chunks:
                key = chunk.chunk_id or f"{chunk.page}:{chunk.text[:120]}"
                if key in seen:
                    continue
                seen.add(key)
                unique.append(chunk)
            all_chunks = unique

        def _page_key(chunk: RetrievedChunk) -> tuple[int, str]:
            page = chunk.page
            if isinstance(page, int):
                return (page, chunk.chunk_id)
            try:
                return (int(str(page)), chunk.chunk_id)
            except (TypeError, ValueError):
                return (0, chunk.chunk_id)

        return sorted(all_chunks, key=_page_key)

    def list_indexed_documents(self, *, tenant_id: str) -> list[IndexedDocumentEntry]:
        return self._chunk_read.scroll_document_catalog(tenant_id=tenant_id)

    async def list_indexed_documents_async(self, *, tenant_id: str) -> list[IndexedDocumentEntry]:
        return await asyncio.to_thread(self.list_indexed_documents, tenant_id=tenant_id)


class AsyncRetrievalService:
    """Async facade over ``RetrievalService`` for HTTP handlers."""

    def __init__(self, service: RetrievalService) -> None:
        self._service = service

    async def search_documents(
        self, query: str, top_k: int | None = None, *, tenant_id: str
    ) -> list[RetrievedChunk]:
        return await self._service.search_documents_async(query, top_k=top_k, tenant_id=tenant_id)

    async def search_documents_with_meta(
        self, query: str, top_k: int | None = None, *, tenant_id: str
    ) -> SearchDocumentsResult:
        return await self._service.search_documents_with_meta_async(
            query, top_k=top_k, tenant_id=tenant_id
        )

    async def get_source_citation(self, chunk_id: str, *, tenant_id: str) -> SourceCitation:
        return await self._service.get_source_citation_async(chunk_id, tenant_id=tenant_id)

    async def list_indexed_documents(self, *, tenant_id: str) -> list[IndexedDocumentEntry]:
        return await self._service.list_indexed_documents_async(tenant_id=tenant_id)

    async def list_document_chunks(
        self, doc_id: str, *, tenant_id: str, limit: int = 500
    ) -> list[RetrievedChunk]:
        return await self._service.list_document_chunks_async(
            doc_id, tenant_id=tenant_id, limit=limit
        )

    async def list_source_file_chunks(
        self, source_file: str, *, tenant_id: str, limit: int = 500
    ) -> list[RetrievedChunk]:
        return await self._service.list_source_file_chunks_async(
            source_file, tenant_id=tenant_id, limit=limit
        )
