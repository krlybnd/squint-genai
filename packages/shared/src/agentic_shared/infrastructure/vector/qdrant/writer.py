from collections.abc import Sequence
from typing import Any, cast

from qdrant_client.http.models import (
    Distance,
    FilterSelector,
    PointIdsList,
    PointStruct,
    SparseVectorParams,
    VectorParams,
)

from agentic_shared.infrastructure.vector.core.payload import payload_text
from agentic_shared.infrastructure.vector.core.types import VectorPayload
from agentic_shared.infrastructure.vector.qdrant.client import QdrantClient
from agentic_shared.infrastructure.vector.qdrant.sparse import embed_sparse_text


class QdrantVectorWriter[T: VectorPayload]:
    def __init__(self, client: QdrantClient, payload_type: type[T]) -> None:
        self._client = client
        self._payload_type = payload_type

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
        points = self._client._sdk.retrieve(
            collection_name=self._client.collection_name,
            ids=[point_id],
            with_payload=True,
        )
        if not points:
            return None
        raw = points[0].payload or {}
        payload = self._payload_type.model_validate(raw)
        if payload.tenant_id != tenant_id:
            return None
        return payload

    def upsert(self, point_id: str, payload: T, *, vector: list[float]) -> None:
        self.ensure_collection(vector_dim=len(vector))
        text = payload_text(payload)
        sparse = embed_sparse_text(text, model_name=self.sparse_model)
        self.upsert_points(
            [
                PointStruct(
                    id=point_id,
                    vector={
                        self.dense_vector_name: vector,
                        self.sparse_vector_name: sparse,
                    },
                    payload=cast(dict[str, Any], payload.model_dump(mode="json", by_alias=True)),
                )
            ]
        )

    def upsert_points(self, points: list[PointStruct]) -> None:
        self._client._sdk.upsert(
            collection_name=self._client.collection_name,
            points=points,
        )

    def set_payload(self, point_ids: Sequence[str], payload: dict[str, Any]) -> None:
        self._client._sdk.set_payload(
            collection_name=self._client.collection_name,
            payload=payload,
            points=list(point_ids),
        )

    def delete(self, point_id: str, *, tenant_id: str) -> None:
        payload = self.get_by_id(point_id, tenant_id=tenant_id)
        if payload is None:
            return
        self.delete_by_ids([point_id])

    def delete_by_ids(self, point_ids: Sequence[str]) -> None:
        self._client._sdk.delete(
            collection_name=self._client.collection_name,
            points_selector=PointIdsList(points=list(point_ids)),
        )

    def delete_by_filter(self, *, points_selector: FilterSelector) -> None:
        self._client._sdk.delete(
            collection_name=self._client.collection_name,
            points_selector=points_selector,
        )

    def ensure_collection(self, *, vector_dim: int = 1536) -> None:
        collections = [c.name for c in self._client._sdk.get_collections().collections]
        if self._client.collection_name in collections:
            return
        self._client._sdk.create_collection(
            collection_name=self._client.collection_name,
            vectors_config={
                self.dense_vector_name: VectorParams(
                    size=vector_dim,
                    distance=Distance.COSINE,
                ),
            },
            sparse_vectors_config={
                self.sparse_vector_name: SparseVectorParams(),
            },
        )
