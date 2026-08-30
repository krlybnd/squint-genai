from typing import Protocol, runtime_checkable
from uuid import UUID

from agentic_shared.domains.persistence.entities import IndexJob, JobStatus
from agentic_shared.infrastructure.sql.core.protocols import (
    ReadRepository,
    SyncReadRepository,
    SyncWriteRepository,
    WriteRepository,
)


@runtime_checkable
class IndexJobReadRepository(ReadRepository[IndexJob], Protocol):
    async def find_active_for_document(self, document_id: UUID) -> IndexJob | None: ...

    async def get_latest_for_document(self, document_id: UUID) -> IndexJob | None: ...


@runtime_checkable
class IndexJobWriteRepository(WriteRepository[IndexJob], Protocol):
    async def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        *,
        error: str | None = None,
    ) -> None: ...


@runtime_checkable
class IndexJobWriteRepositorySync(
    SyncReadRepository[IndexJob], SyncWriteRepository[IndexJob], Protocol
):
    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        *,
        error: str | None = None,
    ) -> None: ...
