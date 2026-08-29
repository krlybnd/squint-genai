from typing import Protocol, runtime_checkable

from agentic_shared.infrastructure.vector.types import VectorPayload


@runtime_checkable
class VectorReadRepository[T: VectorPayload](Protocol):
    def get_by_id(self, point_id: str, *, tenant_id: str) -> T | None: ...


@runtime_checkable
class VectorWriteRepository[T: VectorPayload](Protocol):
    def get_by_id(self, point_id: str, *, tenant_id: str) -> T | None: ...

    def upsert(self, point_id: str, payload: T, *, vector: list[float]) -> None: ...

    def delete(self, point_id: str, *, tenant_id: str) -> None: ...
