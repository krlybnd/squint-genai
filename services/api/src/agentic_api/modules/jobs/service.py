import logging
import uuid
from datetime import UTC, datetime

from agentic_shared.domains.persistence.entities import IndexJob, JobStatus
from agentic_shared.domains.persistence.protocols.documents import (
    DocumentReadRepository,
    DocumentWriteRepository,
)
from agentic_shared.domains.persistence.protocols.index_jobs import (
    IndexJobReadRepository,
    IndexJobWriteRepository,
)
from agentic_shared.infrastructure.redis.settings import RedisSettings
from celery import Celery

from agentic_api.modules.jobs.settings import get_module_settings as get_jobs_module_settings

# Persisted i18n key — localized when exposed via API (`t_stored`).
JOB_CANCELLED_BY_USER = "jobs.cancelled_by_user"

logger = logging.getLogger(__name__)


class JobService:
    def __init__(
        self,
        tenant_id: str,
        documents_read: DocumentReadRepository,
        documents_write: DocumentWriteRepository,
        jobs_read: IndexJobReadRepository,
        jobs_write: IndexJobWriteRepository,
        settings: RedisSettings,
    ) -> None:
        self._tenant_id = tenant_id
        self._documents_read = documents_read
        self._documents_write = documents_write
        self._jobs_read = jobs_read
        self._jobs_write = jobs_write
        self._settings = settings
        jobs_module = get_jobs_module_settings()
        self._celery = Celery(
            jobs_module.celery_app_name,
            broker=settings.celery_broker_url,
            backend=settings.celery_result_backend,
        )
        self._index_document_task_name = jobs_module.index_document_task_name

    async def enqueue_index_job(
        self,
        job_id: uuid.UUID,
        document_id: uuid.UUID,
        minio_key: str,
        filename: str,
        tenant_id: str | None = None,
    ) -> str:
        tid = tenant_id or self._tenant_id
        result = self._celery.send_task(
            self._index_document_task_name,
            args=[str(job_id), str(document_id), minio_key, filename, tid],
        )
        task_id = result.id
        if not isinstance(task_id, str) or not task_id:
            raise TypeError("celery send_task must return a string id")
        job = await self._jobs_read.get_by_id(job_id)
        if job:
            job.celery_task_id = task_id
            job.status = JobStatus.PENDING
            await self._jobs_write.update(job)
        logger.info(
            "enqueued index job job_id=%s document_id=%s task_id=%s tenant_id=%s",
            job_id,
            document_id,
            task_id,
            tid,
        )
        return task_id

    async def enqueue_reindex_all(self) -> list[uuid.UUID]:
        documents = await self._documents_read.list_ordered_by_created_desc()
        job_ids: list[uuid.UUID] = []
        for doc in documents:
            if await self._jobs_read.find_active_for_document(doc.id):
                continue
            doc.indexed_at = None
            await self._documents_write.update(doc)
            job = IndexJob(
                tenant_id=self._tenant_id,
                document_id=doc.id,
                status=JobStatus.PENDING,
            )
            job = await self._jobs_write.add(job)
            await self.enqueue_index_job(job.id, doc.id, doc.minio_key, doc.filename)
            job_ids.append(job.id)
        logger.info("reindex all queued jobs=%d tenant_id=%s", len(job_ids), self._tenant_id)
        return job_ids

    async def get_job(self, job_id: uuid.UUID) -> IndexJob | None:
        return await self._jobs_read.get_by_id(job_id)

    async def cancel_indexing_for_document(self, document_id: uuid.UUID) -> None:
        """Revoke queued/running Celery work and mark the latest job failed."""
        job = await self._jobs_read.find_active_for_document(document_id)
        if job is None:
            job = await self._jobs_read.get_latest_for_document(document_id)
        if job is None or job.status == JobStatus.COMPLETED:
            return
        if job.celery_task_id:
            self._celery.control.revoke(job.celery_task_id, terminate=True, signal="SIGTERM")
        logger.info(
            "cancelled index job job_id=%s document_id=%s tenant_id=%s",
            job.id,
            document_id,
            self._tenant_id,
        )
        job.status = JobStatus.FAILED
        job.error_message = JOB_CANCELLED_BY_USER
        job.completed_at = datetime.now(UTC)
        await self._jobs_write.update(job)

    async def update_status(
        self,
        job_id: uuid.UUID,
        status: JobStatus,
        *,
        error: str | None = None,
    ) -> None:
        job = await self._jobs_read.get_by_id(job_id)
        if job:
            job.status = status
            job.error_message = error
            if status in (JobStatus.COMPLETED, JobStatus.FAILED):
                job.completed_at = datetime.now(UTC)
            await self._jobs_write.update(job)
