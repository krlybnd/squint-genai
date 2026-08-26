import unittest
import uuid
from unittest.mock import MagicMock, patch

from agentic_shared.domains.indexing.models import IndexDocumentTaskResult
from agentic_shared.domains.persistence.entities import JobStatus
from celery.exceptions import Retry

from agentic_indexing.main import index_document_task


class TestIndexDocumentTask(unittest.TestCase):
    def _task_args(self) -> tuple[str, str, str, str, str]:
        return (
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            "tenant/doc.pdf",
            "doc.pdf",
            "acme",
        )

    def _configure_task_request(self, *, retries: int = 0, max_retries: int = 2) -> None:
        index_document_task.request.retries = retries
        index_document_task.max_retries = max_retries
        index_document_task.retry = MagicMock()

    @patch("agentic_indexing.main._build_use_case")
    @patch("agentic_indexing.main.QdrantClient")
    @patch("agentic_indexing.main.MinioClient")
    @patch("agentic_indexing.main.SessionLocal")
    def test_success_returns_celery_result(
        self,
        mock_session_local: MagicMock,
        mock_minio_client: MagicMock,
        mock_qdrant_client: MagicMock,
        mock_build_use_case: MagicMock,
    ) -> None:
        # Arrange
        session = MagicMock()
        mock_session_local.return_value = session
        minio = MagicMock()
        mock_minio_client.return_value = minio
        qdrant = MagicMock()
        mock_qdrant_client.return_value = qdrant
        use_case = MagicMock()
        document_id = uuid.uuid4()
        use_case.run.return_value = IndexDocumentTaskResult.from_run(
            document_id=document_id, chunk_count=4
        )
        mock_build_use_case.return_value = use_case
        self._configure_task_request()

        # Act
        result = index_document_task.run(*self._task_args())

        # Assert
        use_case.run.assert_called_once()
        call_kwargs = use_case.run.call_args.kwargs
        self.assertTrue(call_kwargs["mark_running"])
        self.assertEqual(result, {"document_id": str(document_id), "chunk_count": 4})
        session.close.assert_called_once()
        minio.close.assert_called_once()
        qdrant.close.assert_called_once()

    @patch("agentic_indexing.main._settings")
    @patch("agentic_indexing.main.SqlAlchemyIndexJobWriteRepositorySync")
    @patch("agentic_indexing.main._build_use_case")
    @patch("agentic_indexing.main.QdrantClient")
    @patch("agentic_indexing.main.MinioClient")
    @patch("agentic_indexing.main.SessionLocal")
    def test_exception_retries_when_attempts_remain(
        self,
        mock_session_local: MagicMock,
        mock_minio_client: MagicMock,
        mock_qdrant_client: MagicMock,
        mock_build_use_case: MagicMock,
        mock_jobs_repo: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        # Arrange
        session = MagicMock()
        mock_session_local.return_value = session
        mock_minio_client.return_value = MagicMock()
        mock_qdrant_client.return_value = MagicMock()
        mock_build_use_case.return_value = MagicMock(
            run=MagicMock(side_effect=RuntimeError("chunk failed"))
        )
        jobs = MagicMock()
        mock_jobs_repo.return_value = jobs
        mock_settings.index_document_retry_countdown = 30
        self._configure_task_request(retries=0, max_retries=2)
        index_document_task.retry.side_effect = Retry()
        job_id, document_id, minio_key, filename, tenant_id = self._task_args()

        # Act / Assert
        with self.assertRaises(Retry):
            index_document_task.run(
                job_id,
                document_id,
                minio_key,
                filename,
                tenant_id,
            )

        # Assert
        session.rollback.assert_called_once()
        jobs.update_status.assert_called_once_with(
            uuid.UUID(job_id),
            JobStatus.RUNNING,
            error="Attempt 1 failed: chunk failed",
        )
        index_document_task.retry.assert_called_once()
        retry_kwargs = index_document_task.retry.call_args.kwargs
        self.assertIsInstance(retry_kwargs["exc"], RuntimeError)
        self.assertEqual(retry_kwargs["countdown"], 30)

    @patch("agentic_indexing.main.SqlAlchemyIndexJobWriteRepositorySync")
    @patch("agentic_indexing.main._build_use_case")
    @patch("agentic_indexing.main.QdrantClient")
    @patch("agentic_indexing.main.MinioClient")
    @patch("agentic_indexing.main.SessionLocal")
    def test_exception_marks_failed_on_terminal_retry(
        self,
        mock_session_local: MagicMock,
        mock_minio_client: MagicMock,
        mock_qdrant_client: MagicMock,
        mock_build_use_case: MagicMock,
        mock_jobs_repo: MagicMock,
    ) -> None:
        # Arrange
        session = MagicMock()
        mock_session_local.return_value = session
        mock_minio_client.return_value = MagicMock()
        mock_qdrant_client.return_value = MagicMock()
        error = RuntimeError("chunk failed")
        mock_build_use_case.return_value = MagicMock(run=MagicMock(side_effect=error))
        jobs = MagicMock()
        mock_jobs_repo.return_value = jobs
        self._configure_task_request(retries=2, max_retries=2)
        job_id, document_id, minio_key, filename, tenant_id = self._task_args()

        # Act / Assert
        with self.assertRaises(RuntimeError):
            index_document_task.run(
                job_id,
                document_id,
                minio_key,
                filename,
                tenant_id,
            )

        # Assert
        session.rollback.assert_called_once()
        jobs.update_status.assert_called_once_with(
            uuid.UUID(job_id),
            JobStatus.FAILED,
            error="chunk failed",
        )
        index_document_task.retry.assert_not_called()


if __name__ == "__main__":
    unittest.main()
