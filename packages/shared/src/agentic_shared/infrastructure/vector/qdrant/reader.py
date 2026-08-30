from typing import Any, cast
from uuid import UUID

from qdrant_client.http.models import Filter, QueryResponse, Record

from agentic_shared.infrastructure.vector.core.types import VectorPayload
from agentic_shared.infrastructure.vector.qdrant.client import QdrantClient

ScrollOffset = str | int | UUID | None


class QdrantVectorReader[T: VectorPayload]:
    def __init__(self, client: QdrantClient, payload_type: type[T]) -> None:
        self._client = client
        self._payload_type = payload_type

    @property
    def default_top_k(self) -> int:
        return self._client.default_top_k

    @property
    def candidate_top_k(self) -> int:
        return self._client.candidate_top_k

    @property
    def sparse_model(self) -> str:
        return self._client.sparse_model

    @property
    def dense_vector_name(self) -> str:
        return self._client.dense_vector_name

    @property
    def sparse_vector_name(self) -> str:
        return self._client.sparse_vector_name

    def get_by_id(self, point_id: str, *, tenant_id: str) -> T | None:
        raw = self.retrieve(point_id)
        if raw is None:
            return None
        payload = self._payload_type.model_validate(raw)
        if payload.tenant_id != tenant_id:
            return None
        return payload

    def retrieve(self, point_id: str) -> dict[str, Any] | None:
        points = self._client._sdk.retrieve(
            collection_name=self._client.collection_name,
            ids=[point_id],
            with_payload=True,
        )
        if not points:
            return None
        return points[0].payload or {}

    def scroll(
        self,
        *,
        scroll_filter: Filter,
        limit: int,
        offset: ScrollOffset = None,
    ) -> tuple[list[Record], ScrollOffset]:
        records, next_offset = self._client._sdk.scroll(
            collection_name=self._client.collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=True,
        )
        return records, cast(ScrollOffset, next_offset)

    def query_points(self, **kwargs: Any) -> QueryResponse:
        return self._client._sdk.query_points(
            collection_name=self._client.collection_name,
            **kwargs,
        )
