import logging
from collections.abc import Sequence
from typing import Any, cast

from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient as QdrantSdkClient
from qdrant_client.http.models import (
    Condition,
    Distance,
    FieldCondition,
    Filter,
    Fusion,
    FusionQuery,
    MatchValue,
    PointStruct,
    Prefetch,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from agentic_shared.domains.annotations.models import ChunkComment
from agentic_shared.domains.retrieval.models import IndexedDocumentEntry, RetrievedChunk
from agentic_shared.infrastructure.core.client import BaseInfraClient
from agentic_shared.infrastructure.vector.comments import normalize_comments
from agentic_shared.infrastructure.vector.dense import embed_dense_texts
from agentic_shared.infrastructure.vector.enums import QdrantPointType
from agentic_shared.infrastructure.vector.payload import payload_page, payload_text
from agentic_shared.infrastructure.vector.protocols import QdrantReader, QdrantWriter
from agentic_shared.infrastructure.vector.settings import QdrantSettings
from agentic_shared.infrastructure.vector.sparse import embed_sparse_text, embed_sparse_texts
from agentic_shared.infrastructure.vector.types import CommentPointPayload
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings

logger = logging.getLogger(__name__)


class QdrantClient(BaseInfraClient[QdrantSettings]):
    def __init__(self, settings: QdrantSettings) -> None:
        super().__init__(settings)
        self._sdk = QdrantSdkClient(url=settings.qdrant_url)

    async def health_check(self) -> bool:
        return self.is_available()

    def close(self) -> None:
        try:
            self._sdk.close()
        finally:
            super().close()

    @property
    def default_top_k(self) -> int:
        return self._settings.top_k

    @property
    def candidate_top_k(self) -> int:
        return self._settings.candidate_top_k

    @property
    def sparse_model(self) -> str:
        return self._settings.sparse_model

    def is_available(self) -> bool:
        try:
            self._sdk.get_collections()
            return True
        except Exception:
            return False

    def retrieve_point(self, point_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        points = self._sdk.retrieve(
            collection_name=self._settings.qdrant_collection,
            ids=[point_id],
            with_payload=True,
        )
        if not points:
            return None
        payload = points[0].payload or {}
        if payload.get("tenant_id") != tenant_id:
            return None
        return payload

    def scroll_document_catalog(self, *, tenant_id: str) -> list[IndexedDocumentEntry]:
        docs: dict[str, IndexedDocumentEntry] = {}
        try:
            offset = None
            while True:
                records, offset = self._sdk.scroll(
                    collection_name=self._settings.qdrant_collection,
                    scroll_filter=self._chunk_only_filter(
                        must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
                    ),
                    limit=100,
                    offset=offset,
                    with_payload=True,
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
            records, next_offset = self._sdk.scroll(
                collection_name=self._settings.qdrant_collection,
                scroll_filter=scroll_filter,
                limit=limit,
                offset=offset,
                with_payload=True,
            )
            for point in records:
                payload = point.payload or {}
                chunks.append(self._payload_to_chunk(str(point.id), payload))
            next_token = str(next_offset) if next_offset is not None else None
            return chunks, next_token
        except Exception:
            logger.warning("qdrant scroll chunks failed", exc_info=True)
            return [], None

    @staticmethod
    def _payload_to_chunk(
        chunk_id: str, payload: dict[str, Any], *, score: float | None = None
    ) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=chunk_id,
            text=payload_text(payload),
            doc_id=payload.get("doc_id"),
            source_file=str(payload.get("source_file") or ""),
            page=payload_page(payload),
            score=score,
            comments=normalize_comments(payload),
        )

    def vector_store(self) -> QdrantVectorStore:
        return QdrantVectorStore(
            client=self._sdk,
            collection_name=self._settings.qdrant_collection,
        )

    def ensure_collection(self, *, vector_dim: int = 1536) -> None:
        collections = [c.name for c in self._sdk.get_collections().collections]
        if self._settings.qdrant_collection in collections:
            return
        self._sdk.create_collection(
            collection_name=self._settings.qdrant_collection,
            vectors_config={
                self._settings.dense_vector_name: VectorParams(
                    size=vector_dim,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                self._settings.sparse_vector_name: SparseVectorParams(),
            },
        )

    def index_nodes(
        self,
        nodes: list[Any],
        *,
        llm: LLMSettings,
        embedding: EmbeddingSettings,
    ) -> int:
        if not nodes:
            return 0

        nodes = [node for node in nodes if node.get_content().strip()]
        if not nodes:
            return 0

        texts = [node.get_content() for node in nodes]
        dense_vectors = embed_dense_texts(texts, llm=llm, embedding=embedding)
        sparse_vectors = embed_sparse_texts(texts, model_name=self._settings.sparse_model)
        vector_dim = len(dense_vectors[0])
        self.ensure_collection(vector_dim=vector_dim)

        points: list[PointStruct] = []
        for node, dense, sparse in zip(nodes, dense_vectors, sparse_vectors, strict=True):
            metadata = node.metadata or {}
            text = node.get_content()
            points.append(
                PointStruct(
                    id=node.node_id,
                    vector={
                        self._settings.dense_vector_name: dense,
                        self._settings.sparse_vector_name: sparse,
                    },
                    payload={
                        "text": text,
                        "doc_id": metadata.get("doc_id"),
                        "source_file": metadata.get("source_file", ""),
                        "page": metadata.get("page", metadata.get("page_label")),
                        "tenant_id": metadata.get("tenant_id"),
                    },
                )
            )

        self._sdk.upsert(collection_name=self._settings.qdrant_collection, points=points)
        logger.info("indexed qdrant points count=%d", len(points))
        return len(points)

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
            response = self._sdk.query_points(
                collection_name=self._settings.qdrant_collection,
                prefetch=[
                    Prefetch(
                        query=dense_vector,
                        using=self._settings.dense_vector_name,
                        limit=limit,
                        filter=Filter(must=[tenant_filter]),
                    ),
                    Prefetch(
                        query=sparse_vector,
                        using=self._settings.sparse_vector_name,
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
            payload = point.payload or {}
            chunk = self._payload_to_chunk(str(point.id), payload, score=point.score)
            chunks.append(chunk)
        return chunks

    def append_chunk_comment(self, chunk_id: str, comment: ChunkComment) -> None:
        points = self._sdk.retrieve(
            collection_name=self._settings.qdrant_collection,
            ids=[chunk_id],
            with_payload=True,
        )
        if not points:
            raise ValueError(f"chunk not found: {chunk_id}")
        payload = points[0].payload or {}
        comments = normalize_comments(payload)
        comments.append(comment)
        self._sdk.set_payload(
            collection_name=self._settings.qdrant_collection,
            payload={"comments": [c.model_dump(mode="json") for c in comments]},
            points=[chunk_id],
        )

    def upsert_comment_vector(
        self,
        comment_id: str,
        vector: list[float],
        payload: CommentPointPayload,
    ) -> None:
        self.ensure_collection(vector_dim=len(vector))
        text = payload_text(payload)
        sparse = embed_sparse_text(text, model_name=self._settings.sparse_model)
        self._sdk.upsert(
            collection_name=self._settings.qdrant_collection,
            points=[
                PointStruct(
                    id=comment_id,
                    vector={
                        self._settings.dense_vector_name: vector,
                        self._settings.sparse_vector_name: sparse,
                    },
                    payload=cast(dict[str, Any], payload),
                )
            ],
        )


class QdrantVectorReader(QdrantReader):
    def __init__(self, client: QdrantClient) -> None:
        self._client = client

    @property
    def title(self) -> str:
        return self._client.title

    async def health_check(self) -> bool:
        return await self._client.health_check()

    @property
    def default_top_k(self) -> int:
        return self._client.default_top_k

    @property
    def candidate_top_k(self) -> int:
        return self._client.candidate_top_k

    @property
    def sparse_model(self) -> str:
        return self._client.sparse_model

    def is_available(self) -> bool:
        return self._client.is_available()

    def retrieve_point(self, point_id: str, *, tenant_id: str) -> dict[str, Any] | None:
        return self._client.retrieve_point(point_id, tenant_id=tenant_id)

    def scroll_document_catalog(self, *, tenant_id: str) -> list[IndexedDocumentEntry]:
        return self._client.scroll_document_catalog(tenant_id=tenant_id)

    def scroll_document_chunks(
        self,
        doc_id: str,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: str | None = None,
    ) -> tuple[list[RetrievedChunk], str | None]:
        return self._client.scroll_document_chunks(
            doc_id, tenant_id=tenant_id, limit=limit, offset=offset
        )

    def scroll_source_file_chunks(
        self,
        source_file: str,
        *,
        tenant_id: str,
        limit: int = 100,
        offset: str | None = None,
    ) -> tuple[list[RetrievedChunk], str | None]:
        return self._client.scroll_source_file_chunks(
            source_file, tenant_id=tenant_id, limit=limit, offset=offset
        )

    def hybrid_search(
        self,
        *,
        tenant_id: str,
        dense_vector: list[float],
        sparse_vector: SparseVector,
        limit: int,
    ) -> list[RetrievedChunk]:
        return self._client.hybrid_search(
            tenant_id=tenant_id,
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            limit=limit,
        )


class QdrantVectorWriter(QdrantWriter):
    def __init__(self, client: QdrantClient) -> None:
        self._client = client

    def ensure_collection(self, *, vector_dim: int = 1536) -> None:
        self._client.ensure_collection(vector_dim=vector_dim)

    def index_nodes(
        self,
        nodes: list[Any],
        *,
        llm: LLMSettings,
        embedding: EmbeddingSettings,
    ) -> int:
        return self._client.index_nodes(nodes, llm=llm, embedding=embedding)

    def append_chunk_comment(self, chunk_id: str, comment: ChunkComment) -> None:
        self._client.append_chunk_comment(chunk_id, comment)

    def upsert_comment_vector(
        self,
        comment_id: str,
        vector: list[float],
        payload: CommentPointPayload,
    ) -> None:
        self._client.upsert_comment_vector(comment_id, vector, payload)
