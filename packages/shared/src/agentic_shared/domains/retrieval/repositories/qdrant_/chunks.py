import logging
from collections.abc import Sequence
from typing import Any, cast

from qdrant_client.http.models import (
    Condition,
    FieldCondition,
    Filter,
    FilterSelector,
    Fusion,
    FusionQuery,
    MatchValue,
    PointStruct,
    Prefetch,
    SparseVector,
)

from agentic_shared.domains.retrieval.models import (
    ChunkPointPayload,
    IndexedDocumentEntry,
    RetrievedChunk,
)
from agentic_shared.domains.retrieval.protocols.chunks import (
    ChunkReadRepository,
    ChunkWriteRepository,
)
from agentic_shared.infrastructure.vector.core.payload import payload_page, payload_text
from agentic_shared.infrastructure.vector.qdrant.client import QdrantClient
from agentic_shared.infrastructure.vector.qdrant.dense import embed_dense_texts
from agentic_shared.infrastructure.vector.qdrant.enums import QdrantPointType
from agentic_shared.infrastructure.vector.qdrant.reader import QdrantVectorReader
from agentic_shared.infrastructure.vector.qdrant.sparse import embed_sparse_texts
from agentic_shared.infrastructure.vector.qdrant.writer import QdrantVectorWriter
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings

logger = logging.getLogger(__name__)


def chunk_payload_to_retrieved(
    chunk_id: str,
    payload: ChunkPointPayload,
    *,
    score: float | None = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        text=payload_text(payload),
        doc_id=payload.doc_id,
        source_file=payload.source_file or "",
        page=payload_page(payload),
        score=score,
        comments=list(payload.comments) or None,
    )


class QdrantChunkReadRepository(QdrantVectorReader[ChunkPointPayload], ChunkReadRepository):
    def __init__(self, client: QdrantClient) -> None:
        super().__init__(client, ChunkPointPayload)

    def scroll_document_catalog(self, *, tenant_id: str) -> list[IndexedDocumentEntry]:
        docs: dict[str, IndexedDocumentEntry] = {}
        try:
            offset = None
            while True:
                records, offset = self.scroll(
                    scroll_filter=self._chunk_only_filter(
                        must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
                    ),
                    limit=100,
                    offset=offset,
                )
                for point in records:
                    payload = point.payload or {}
                    if payload.get("point_type") == QdrantPointType.COMMENT:
                        continue
                    doc_id = payload.get("doc_id", "unknown")
                    if doc_id not in docs:
                        docs[doc_id] = IndexedDocumentEntry(
                            doc_id=str(doc_id),
                            source_file=str(payload.get("source_file") or ""),
                            chunk_count=0,
                        )
                    entry = docs[doc_id]
                    docs[doc_id] = entry.model_copy(update={"chunk_count": entry.chunk_count + 1})
                if offset is None:
                    break
        except Exception:
            logger.warning(
                "qdrant scroll catalog failed tenant_id=%s",
                tenant_id,
                exc_info=True,
            )
        return list(docs.values())

    def scroll_document_chunks(
        self,
        doc_id: str,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: str | None = None,
    ) -> tuple[list[RetrievedChunk], str | None]:
        return self._scroll_chunks(
            self._chunk_only_filter(
                must=[
                    FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
                    FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
                ]
            ),
            limit=limit,
            offset=offset,
        )

    def scroll_source_file_chunks(
        self,
        source_file: str,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: str | None = None,
    ) -> tuple[list[RetrievedChunk], str | None]:
        return self._scroll_chunks(
            self._chunk_only_filter(
                must=[
                    FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
                    FieldCondition(key="source_file", match=MatchValue(value=source_file)),
                ]
            ),
            limit=limit,
            offset=offset,
        )

    def hybrid_search(
        self,
        *,
        tenant_id: str,
        dense_vector: list[float],
        sparse_vector: SparseVector,
        limit: int,
    ) -> list[RetrievedChunk]:
        tenant_filter = FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
        try:
            response = self.query_points(
                prefetch=[
                    Prefetch(
                        query=dense_vector,
                        using=self.dense_vector_name,
                        limit=limit,
                        filter=Filter(must=[tenant_filter]),
                    ),
                    Prefetch(
                        query=sparse_vector,
                        using=self.sparse_vector_name,
                        limit=limit,
                        filter=Filter(must=[tenant_filter]),
                    ),
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                query_filter=Filter(must=[tenant_filter]),
                limit=limit,
                with_payload=True,
            )
        except Exception:
            logger.warning(
                "qdrant hybrid search failed tenant_id=%s",
                tenant_id,
                exc_info=True,
            )
            return []

        chunks: list[RetrievedChunk] = []
        for point in response.points:
            payload = ChunkPointPayload.model_validate(point.payload or {})
            chunks.append(chunk_payload_to_retrieved(str(point.id), payload, score=point.score))
        return chunks

    @staticmethod
    def _chunk_only_filter(*, must: Sequence[FieldCondition]) -> Filter:
        must_conditions: list[Condition] = list(must)
        must_not_conditions: list[Condition] = [
            FieldCondition(key="point_type", match=MatchValue(value=QdrantPointType.COMMENT))
        ]
        return Filter(must=must_conditions, must_not=must_not_conditions)

    def _scroll_chunks(
        self,
        scroll_filter: Filter,
        *,
        limit: int = 100,
        offset: str | None = None,
    ) -> tuple[list[RetrievedChunk], str | None]:
        chunks: list[RetrievedChunk] = []
        try:
            records, next_offset = self.scroll(
                scroll_filter=scroll_filter,
                limit=limit,
                offset=offset,
            )
            for point in records:
                payload = ChunkPointPayload.model_validate(point.payload or {})
                chunks.append(chunk_payload_to_retrieved(str(point.id), payload))
            next_token = str(next_offset) if next_offset is not None else None
            return chunks, next_token
        except Exception:
            logger.warning("qdrant scroll chunks failed", exc_info=True)
            return [], None


class QdrantChunkWriteRepository(QdrantVectorWriter[ChunkPointPayload], ChunkWriteRepository):
    def __init__(self, client: QdrantClient) -> None:
        super().__init__(client, ChunkPointPayload)
        self._read = QdrantChunkReadRepository(client)

    def index_nodes(
        self,
        nodes: list[Any],
        *,
        llm: LiteLLMChatSettings,
        embedding: LiteLLMEmbeddingSettings,
    ) -> int:
        if not nodes:
            return 0

        nodes = [node for node in nodes if node.get_content().strip()]
        if not nodes:
            return 0

        texts = [node.get_content() for node in nodes]
        dense_vectors = embed_dense_texts(texts, llm=llm, embedding=embedding)
        sparse_vectors = embed_sparse_texts(texts, model_name=self.sparse_model)
        vector_dim = len(dense_vectors[0])
        self.ensure_collection(vector_dim=vector_dim)

        points: list[PointStruct] = []
        for node, dense, sparse in zip(nodes, dense_vectors, sparse_vectors, strict=True):
            metadata = node.metadata or {}
            payload = ChunkPointPayload(
                text=node.get_content(),
                doc_id=metadata.get("doc_id"),
                source_file=metadata.get("source_file") or "",
                page=metadata.get("page", metadata.get("page_label")),
                tenant_id=metadata.get("tenant_id"),
            )
            points.append(
                PointStruct(
                    id=node.node_id,
                    vector={
                        self.dense_vector_name: dense,
                        self.sparse_vector_name: sparse,
                    },
                    payload=cast(
                        dict[str, Any],
                        payload.model_dump(mode="json", by_alias=True),
                    ),
                )
            )

        self.upsert_points(points)
        logger.info("indexed qdrant points count=%d", len(points))
        return len(points)

    def delete_by_doc_id(self, doc_id: str, *, tenant_id: str) -> None:
        try:
            self.delete_by_filter(
                points_selector=FilterSelector(
                    filter=self._read._chunk_only_filter(
                        must=[
                            FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id)),
                            FieldCondition(key="doc_id", match=MatchValue(value=doc_id)),
                        ]
                    )
                ),
            )
            logger.info(
                "deleted qdrant vectors doc_id=%s tenant_id=%s",
                doc_id,
                tenant_id,
            )
        except Exception:
            logger.warning(
                "qdrant delete document vectors failed doc_id=%s tenant_id=%s",
                doc_id,
                tenant_id,
                exc_info=True,
            )
