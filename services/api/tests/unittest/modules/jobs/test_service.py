import unittest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from agentic_shared.domains.persistence.entities import Document, IndexJob, JobStatus
from agentic_shared.infrastructure.cache.redis.settings import RedisSettings

from agentic_api.modules.jobs.service import JOB_CANCELLED_BY_USER, JobService


def _document(**overrides: object) -> Document:
    doc_id = overrides.pop("id", uuid4())
    return Document(
        id=doc_id,
        tenant_id=overrides.pop("tenant_id", "tenant-1"),
        filename=overrides.pop("filename", "paper.pdf"),
        minio_key=overrides.pop("minio_key", f"pdfs/tenant-1/{doc_id}/paper.pdf"),
        **overrides,
    )


def _job(**overrides: object) -> IndexJob:
    return IndexJob(
        id=overrides.pop("id", uuid4()),
        tenant_id=overrides.pop("tenant_id", "tenant-1"),
        document_id=overrides.pop("document_id", uuid4()),
        status=overrides.pop("status", JobStatus.PENDING),
        celery_task_id=overrides.pop("celery_task_id", None),
        **overrides,
    )


@patch("agentic_api.modules.jobs.service.Celery")
class TestJobService(unittest.IsolatedAsyncioTestCase):
    def _service(self, mock_celery_cls: Mock, **overrides: object) -> JobService:
        mock_celery = mock_celery_cls.return_value
        mock_celery.control = Mock()
        defaults = {
            "tenant_id": "tenant-1",
            "documents_read": AsyncMock(),
            "documents_write": AsyncMock(),
            "jobs_read": AsyncMock(),
            "jobs_write": AsyncMock(),
            "settings": RedisSettings(),
        }
        defaults.update(overrides)
        service = JobService(**defaults)
        service._celery = mock_celery
        return service

    async def test_enqueue_index_job_sends_task_and_updates_job(
        self, mock_celery_cls: Mock
    ) -> None:
        # Arrange
        service = self._service(mock_celery_cls)
        job = _job(celery_task_id=None)
        send_result = Mock(id="celery-task-1")
        service._celery.send_task.return_value = send_result
        service._jobs_read.get_by_id.return_value = job
        document = _document()

        # Act
        task_id = await service.enqueue_index_job(
            job.id,
            document.id,
            document.minio_key,
            document.filename,
        )

        # Assert
        self.assertEqual(task_id, "celery-task-1")
        service._celery.send_task.assert_called_once()
        self.assertEqual(job.celery_task_id, "celery-task-1")
        self.assertEqual(job.status, JobStatus.PENDING)
        service._jobs_write.update.assert_awaited_once_with(job)

    async def test_enqueue_reindex_all_skips_documents_with_active_job(
        self, mock_celery_cls: Mock
    ) -> None:
        # Arrange
        service = self._service(mock_celery_cls)
        active_doc = _document()
        idle_doc = _document()
        service._documents_read.list_ordered_by_created_desc.return_value = [
            active_doc,
            idle_doc,
        ]

        async def find_active(document_id: object) -> IndexJob | None:
            if document_id == active_doc.id:
                return _job(document_id=active_doc.id, status=JobStatus.RUNNING)
            return None

        service._jobs_read.find_active_for_document.side_effect = find_active
        created_job = _job(document_id=idle_doc.id)
        service._jobs_write.add.return_value = created_job
        send_result = Mock(id="celery-task-2")
        service._celery.send_task.return_value = send_result
        service._jobs_read.get_by_id.return_value = created_job

        # Act
        job_ids = await service.enqueue_reindex_all()

        # Assert
        self.assertEqual(job_ids, [created_job.id])
        service._documents_write.update.assert_awaited_once()
        updated_doc = service._documents_write.update.await_args.args[0]
        self.assertEqual(updated_doc.id, idle_doc.id)
        self.assertIsNone(updated_doc.indexed_at)
        service._jobs_write.add.assert_awaited_once()
        service._celery.send_task.assert_called_once()

    async def test_cancel_indexing_for_document_revokes_and_marks_failed(
        self, mock_celery_cls: Mock
    ) -> None:
        # Arrange
        service = self._service(mock_celery_cls)
        job = _job(status=JobStatus.RUNNING, celery_task_id="task-99")
        service._jobs_read.find_active_for_document.return_value = job

        # Act
        await service.cancel_indexing_for_document(job.document_id)

        # Assert
        service._celery.control.revoke.assert_called_once_with(
            "task-99",
            terminate=True,
            signal="SIGTERM",
        )
        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertEqual(job.error_message, JOB_CANCELLED_BY_USER)
        self.assertIsNotNone(job.completed_at)
        service._jobs_write.update.assert_awaited_once_with(job)

    async def test_cancel_indexing_for_document_noop_when_completed(
        self, mock_celery_cls: Mock
    ) -> None:
        # Arrange
        service = self._service(mock_celery_cls)
        job = _job(status=JobStatus.COMPLETED)
        service._jobs_read.find_active_for_document.return_value = None
        service._jobs_read.get_latest_for_document.return_value = job

        # Act
        await service.cancel_indexing_for_document(job.document_id)

        # Assert
        service._celery.control.revoke.assert_not_called()
        service._jobs_write.update.assert_not_awaited()

    async def test_update_status_sets_completed_at_for_terminal_states(
        self, mock_celery_cls: Mock
    ) -> None:
        # Arrange
        service = self._service(mock_celery_cls)
        completed_job = _job(status=JobStatus.RUNNING)
        failed_job = _job(status=JobStatus.RUNNING)
        pending_job = _job(status=JobStatus.PENDING)

        async def get_by_id(job_id: object) -> IndexJob | None:
            if job_id == completed_job.id:
                return completed_job
            if job_id == failed_job.id:
                return failed_job
            if job_id == pending_job.id:
                return pending_job
            return None

        service._jobs_read.get_by_id.side_effect = get_by_id

        # Act
        await service.update_status(completed_job.id, JobStatus.COMPLETED)
        await service.update_status(failed_job.id, JobStatus.FAILED, error="boom")
        await service.update_status(pending_job.id, JobStatus.RUNNING)

        # Assert
        self.assertIsNotNone(completed_job.completed_at)
        self.assertIsNotNone(failed_job.completed_at)
        self.assertEqual(failed_job.error_message, "boom")
        self.assertIsNone(pending_job.completed_at)


if __name__ == "__main__":
    unittest.main()
