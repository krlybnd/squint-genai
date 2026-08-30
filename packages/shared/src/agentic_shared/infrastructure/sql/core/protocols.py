from typing import Protocol, TypeVar, runtime_checkable
from uuid import UUID

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class ReadRepository(Protocol[T_co]):
    async def get_by_id(self, entity_id: UUID) -> T_co | None: ...


@runtime_checkable
class WriteRepository(Protocol[T]):
    async def add(self, entity: T) -> T: ...

    async def get_by_id(self, entity_id: UUID) -> T | None: ...

    async def update(self, entity: T) -> T: ...

    async def delete(self, entity_id: UUID) -> None: ...


@runtime_checkable
class SyncReadRepository(Protocol[T_co]):
    def get_by_id(self, entity_id: UUID) -> T_co | None: ...


@runtime_checkable
class SyncWriteRepository(Protocol[T]):
    def get_by_id(self, entity_id: UUID) -> T | None: ...

    def update(self, entity: T) -> T: ...
