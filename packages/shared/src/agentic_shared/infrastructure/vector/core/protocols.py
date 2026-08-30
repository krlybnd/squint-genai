from typing import Protocol, runtime_checkable

from agentic_shared.infrastructure.vector.core.types import VectorPayload


@runtime_checkable
class VectorReader[T: VectorPayload](Protocol):
    def get_by_id(self, point_id: str, *, tenant_id: str) -> T | None: ...


@runtime_checkable
class VectorWriter[T: VectorPayload](Protocol):
    def get_by_id(self, point_id: str, *, tenant_id: str) -> T | None: ...

    def upsert(self, point_id: str, payload: T, *, vector: list[float]) -> None: ...

    def delete(self, point_id: str, *, tenant_id: str) -> None: ...
