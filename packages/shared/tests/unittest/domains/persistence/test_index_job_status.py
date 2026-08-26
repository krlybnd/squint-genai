import unittest
from datetime import UTC, datetime
from uuid import uuid4

from agentic_shared.domains.persistence.entities.index_job import IndexJob, JobStatus
from agentic_shared.domains.persistence.index_job_status import apply_index_job_status


class TestApplyIndexJobStatus(unittest.TestCase):
    def _job(self) -> IndexJob:
        return IndexJob(
            id=uuid4(),
            tenant_id="tenant-1",
            document_id=uuid4(),
            status=JobStatus.PENDING,
            error_message=None,
            completed_at=None,
        )

    def test_running_sets_status_without_completed_at(self) -> None:
        # Arrange
        job = self._job()

        # Act
        apply_index_job_status(job, JobStatus.RUNNING, error=None)

        # Assert
        self.assertEqual(job.status, JobStatus.RUNNING)
        self.assertIsNone(job.error_message)
        self.assertIsNone(job.completed_at)

    def test_completed_sets_completed_at_and_clears_error(self) -> None:
        # Arrange
        job = self._job()
        before = datetime.now(UTC)

        # Act
        apply_index_job_status(job, JobStatus.COMPLETED)
        after = datetime.now(UTC)

        # Assert
        self.assertEqual(job.status, JobStatus.COMPLETED)
        self.assertIsNone(job.error_message)
        self.assertIsNotNone(job.completed_at)
        assert job.completed_at is not None
        self.assertGreaterEqual(job.completed_at, before)
        self.assertLessEqual(job.completed_at, after)

    def test_failed_stores_error_and_completed_at(self) -> None:
        # Arrange
        job = self._job()

        # Act
        apply_index_job_status(job, JobStatus.FAILED, error="indexing timeout")

        # Assert
        self.assertEqual(job.status, JobStatus.FAILED)
        self.assertEqual(job.error_message, "indexing timeout")
        self.assertIsNotNone(job.completed_at)


if __name__ == "__main__":
    unittest.main()
