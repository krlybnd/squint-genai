from typing import Protocol, runtime_checkable

from agentic_shared.domains.persistence.entities import Document
from agentic_shared.infrastructure.postgres.protocols import (
    ReadRepository,
    SyncWriteRepository,
    WriteRepository,
)


@runtime_checkable
class DocumentReadRepository(ReadRepository[Document], Protocol):
    async def list_ordered_by_created_desc(self, *, limit: int = 500) -> list[Document]: ...


@runtime_checkable
class DocumentWriteRepository(WriteRepository[Document], Protocol):
    pass


@runtime_checkable
class DocumentWriteRepositorySync(SyncWriteRepository[Document], Protocol):
    pass
