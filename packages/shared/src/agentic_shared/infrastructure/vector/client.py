import logging
from collections.abc import Sequence
from typing import Any, cast
from uuid import UUID

from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient as QdrantSdkClient
from qdrant_client.http.models import (
    Distance,
    Filter,
    FilterSelector,
    PointIdsList,
    PointStruct,
    QueryResponse,
    Record,
    SparseVectorParams,
    VectorParams,
)

from agentic_shared.infrastructure.core.client import BaseInfraClient
from agentic_shared.infrastructure.vector.settings import QdrantSettings

logger = logging.getLogger(__name__)

ScrollOffset = str | int | UUID | None


class QdrantClient(BaseInfraClient[QdrantSettings]):
    """Thin Qdrant SDK wrapper. Domain logic lives in vector repositories."""

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

    @property
    def collection_name(self) -> str:
        return self._settings.qdrant_collection

    @property
    def dense_vector_name(self) -> str:
        return self._settings.dense_vector_name

    @property
    def sparse_vector_name(self) -> str:
        return self._settings.sparse_vector_name

    def is_available(self) -> bool:
        try:
            self._sdk.get_collections()
            return True
        except Exception:
            return False

    def retrieve(self, point_id: str) -> dict[str, Any] | None:
        points = self._sdk.retrieve(
            collection_name=self._settings.qdrant_collection,
            ids=[point_id],
            with_payload=True,
        )
        if not points:
            return None
        return points[0].payload or {}

    def upsert(self, points: list[PointStruct]) -> None:
        self._sdk.upsert(collection_name=self._settings.qdrant_collection, points=points)

    def set_payload(self, point_ids: Sequence[str], payload: dict[str, Any]) -> None:
        self._sdk.set_payload(
            collection_name=self._settings.qdrant_collection,
            payload=payload,
            points=list(point_ids),
        )

    def scroll(
        self,
        *,
        scroll_filter: Filter,
        limit: int,
        offset: ScrollOffset = None,
    ) -> tuple[list[Record], ScrollOffset]:
        records, next_offset = self._sdk.scroll(
            collection_name=self._settings.qdrant_collection,
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
        )
        return records, cast(ScrollOffset, next_offset)

    def query_points(self, **kwargs: Any) -> QueryResponse:
        return self._sdk.query_points(collection_name=self._settings.qdrant_collection, **kwargs)

    def delete(self, *, points_selector: FilterSelector) -> None:
        self._sdk.delete(
            collection_name=self._settings.qdrant_collection,
            points_selector=points_selector,
        )

    def delete_by_ids(self, point_ids: Sequence[str]) -> None:
        self._sdk.delete(
            collection_name=self._settings.qdrant_collection,
            points_selector=PointIdsList(points=list(point_ids)),
        )

    def vector_store(self) -> QdrantVectorStore:
        return QdrantVectorStore(
            client=self._sdk,
            collection_name=self._settings.qdrant_collection,
        )

    def ensure_collection(self, *, vector_dim: int = 1536) -> None:
        collections = [collection.name for collection in self._sdk.get_collections().collections]
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
