from uuid import UUID

from sqlalchemy.orm import Session

from agentic_shared.domains.persistence.entities import Document, IndexJob, JobStatus
from agentic_shared.domains.persistence.index_job_status import apply_index_job_status
from agentic_shared.infrastructure.sql.core.repository import SqlAlchemySyncWriteRepository


class SqlAlchemyDocumentWriteRepositorySync(SqlAlchemySyncWriteRepository[Document]):
    def __init__(self, session: Session, tenant_id: str) -> None:
        super().__init__(session, Document, tenant_id)


class SqlAlchemyIndexJobWriteRepositorySync(SqlAlchemySyncWriteRepository[IndexJob]):
    def __init__(self, session: Session, tenant_id: str) -> None:
        super().__init__(session, IndexJob, tenant_id)

    def update_status(
        self,
        job_id: UUID,
        status: JobStatus,
        *,
        error: str | None = None,
    ) -> None:
        job = self.get_by_id(job_id)
        if not job:
            return
        apply_index_job_status(job, status, error=error)
        self._session.commit()
