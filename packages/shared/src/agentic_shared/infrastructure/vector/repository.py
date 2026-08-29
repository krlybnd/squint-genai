from typing import Any, cast

from qdrant_client.http.models import PointStruct

from agentic_shared.infrastructure.vector.client import QdrantClient
from agentic_shared.infrastructure.vector.payload import payload_text
from agentic_shared.infrastructure.vector.sparse import embed_sparse_text
from agentic_shared.infrastructure.vector.types import VectorPayload


class QdrantReadRepository[T: VectorPayload]:
    def __init__(self, client: QdrantClient, payload_type: type[T]) -> None:
        self._client = client
        self._payload_type = payload_type

    def get_by_id(self, point_id: str, *, tenant_id: str) -> T | None:
        raw = self._client.retrieve(point_id)
        if raw is None:
            return None
        payload = self._payload_type.model_validate(raw)
        if payload.tenant_id != tenant_id:
            return None
        return payload


class QdrantWriteRepository[T: VectorPayload]:
    def __init__(self, client: QdrantClient, payload_type: type[T]) -> None:
        self._client = client
        self._payload_type = payload_type

    def get_by_id(self, point_id: str, *, tenant_id: str) -> T | None:
        raw = self._client.retrieve(point_id)
        if raw is None:
            return None
        payload = self._payload_type.model_validate(raw)
        if payload.tenant_id != tenant_id:
            return None
        return payload

    def upsert(self, point_id: str, payload: T, *, vector: list[float]) -> None:
        self._client.ensure_collection(vector_dim=len(vector))
        text = payload_text(payload)
        sparse = embed_sparse_text(text, model_name=self._client.sparse_model)
        self._client.upsert(
            [
                PointStruct(
                    id=point_id,
                    vector={
                        self._client.dense_vector_name: vector,
                        self._client.sparse_vector_name: sparse,
                    },
                    payload=cast(dict[str, Any], payload.model_dump(mode="json", by_alias=True)),
                )
            ]
        )

    def delete(self, point_id: str, *, tenant_id: str) -> None:
        payload = self.get_by_id(point_id, tenant_id=tenant_id)
        if payload is None:
            return
        self._client.delete_by_ids([point_id])
