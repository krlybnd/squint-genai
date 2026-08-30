from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agentic_shared.domains.persistence.entities import IndexJob, JobStatus
from agentic_shared.domains.persistence.index_job_status import apply_index_job_status
from agentic_shared.infrastructure.sql.core.repository import (
    SqlAlchemyReadRepository,
    SqlAlchemyWriteRepository,
)


class SqlAlchemyIndexJobReadRepository(SqlAlchemyReadRepository[IndexJob]):
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        super().__init__(session, IndexJob, tenant_id)

    async def find_active_for_document(self, document_id: UUID) -> IndexJob | None:
        result = await self._session.execute(
            select(IndexJob).where(
                IndexJob.document_id == document_id,
                IndexJob.tenant_id == self._tenant_id,
                IndexJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING]),
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_for_document(self, document_id: UUID) -> IndexJob | None:
        result = await self._session.execute(
            select(IndexJob)
            .where(
                IndexJob.document_id == document_id,
                IndexJob.tenant_id == self._tenant_id,
            )
            .order_by(IndexJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class SqlAlchemyIndexJobWriteRepository(SqlAlchemyWriteRepository[IndexJob]):
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        super().__init__(session, IndexJob, tenant_id)

    async def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        *,
        error: str | None = None,
    ) -> None:
        job = await self.get_by_id(job_id)
        if not job:
            return
        apply_index_job_status(job, status, error=error)
        await self._session.commit()
