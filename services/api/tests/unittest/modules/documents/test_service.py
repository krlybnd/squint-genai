import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from agentic_shared.core.domain_errors import BadRequestError, ConflictError, NotFoundError
from agentic_shared.domains.documents.enums import IndexStatus
from agentic_shared.domains.persistence.entities import Document, IndexJob, JobStatus

from agentic_api.modules.documents.service import DocumentService


def _document(**overrides: object) -> Document:
    doc_id = overrides.pop("id", uuid4())
    return Document(
        id=doc_id,
        tenant_id=overrides.pop("tenant_id", "tenant-1"),
        filename=overrides.pop("filename", "paper.pdf"),
        minio_key=overrides.pop("minio_key", f"pdfs/tenant-1/{doc_id}/paper.pdf"),
        **overrides,
    )


def _service(**overrides: object) -> DocumentService:
    defaults = {
        "tenant_id": "tenant-1",
        "documents_read": AsyncMock(),
        "documents_write": AsyncMock(),
        "jobs_read": AsyncMock(),
        "jobs_write": AsyncMock(),
        "storage_read": Mock(),
        "storage_write": Mock(),
        "qdrant_write": Mock(),
        "job_service": AsyncMock(),
    }
    defaults.update(overrides)
    return DocumentService(**defaults)


class TestDocumentService(unittest.IsolatedAsyncioTestCase):
    async def test_upload_bytes_raises_not_found_when_document_missing(self) -> None:
        # Arrange
        service = _service()
        doc_id = uuid4()
        service._documents_read.get_by_id.return_value = None

        # Act / Assert
        with self.assertRaises(NotFoundError):
            await service.upload_bytes(doc_id, b"pdf-bytes")

    async def test_upload_bytes_raises_bad_request_when_empty(self) -> None:
        # Arrange
        service = _service()
        document = _document()
        service._documents_read.get_by_id.return_value = document

        # Act / Assert
        with self.assertRaises(BadRequestError):
            await service.upload_bytes(document.id, b"")

        # Assert
        service._storage_write.upload.assert_not_called()

    async def test_complete_upload_raises_not_found(self) -> None:
        # Arrange
        service = _service()
        doc_id = uuid4()
        service._documents_read.get_by_id.return_value = None

        # Act / Assert
        with self.assertRaises(NotFoundError):
            await service.complete_upload(doc_id)

    async def test_complete_upload_raises_bad_request_when_object_missing(self) -> None:
        # Arrange
        service = _service()
        document = _document()
        service._documents_read.get_by_id.return_value = document
        service._storage_read.object_exists.return_value = False

        # Act / Assert
        with self.assertRaises(BadRequestError):
            await service.complete_upload(document.id)

    async def test_complete_upload_raises_conflict_when_active_job(self) -> None:
        # Arrange
        service = _service()
        document = _document()
        service._documents_read.get_by_id.return_value = document
        service._storage_read.object_exists.return_value = True
        service._jobs_read.find_active_for_document.return_value = IndexJob(
            tenant_id="tenant-1",
            document_id=document.id,
            status=JobStatus.PENDING,
        )

        # Act / Assert
        with self.assertRaises(ConflictError):
            await service.complete_upload(document.id)

        # Assert
        service._jobs_write.add.assert_not_awaited()

    async def test_reindex_document_cancels_clears_index_and_enqueues(self) -> None:
        # Arrange
        service = _service()
        document = _document(indexed_at=datetime.now(UTC))
        job = IndexJob(
            id=uuid4(),
            tenant_id="tenant-1",
            document_id=document.id,
            status=JobStatus.PENDING,
        )
        service._documents_read.get_by_id.return_value = document
        service._storage_read.object_exists.return_value = True
        service._jobs_write.add.return_value = job

        # Act
        returned_doc, returned_job = await service.reindex_document(document.id)

        # Assert
        service._job_service.cancel_indexing_for_document.assert_awaited_once_with(document.id)
        service._qdrant_write.delete_document_vectors.assert_called_once_with(
            str(document.id),
            tenant_id="tenant-1",
        )
        service._documents_write.update.assert_awaited_once()
        self.assertIsNone(returned_doc.indexed_at)
        service._jobs_write.add.assert_awaited_once()
        service._job_service.enqueue_index_job.assert_awaited_once_with(
            job.id,
            document.id,
            document.minio_key,
            document.filename,
            "tenant-1",
        )
        self.assertIs(returned_job, job)

    async def test_delete_document_removes_qdrant_vectors(self) -> None:
        # Arrange
        service = _service()
        document = _document()
        service._documents_read.get_by_id.return_value = document
        service._storage_read.object_exists.return_value = True

        # Act
        await service.delete_document(document.id)

        # Assert
        service._qdrant_write.delete_document_vectors.assert_called_once_with(
            str(document.id),
            tenant_id="tenant-1",
        )
        service._documents_write.delete.assert_awaited_once_with(document.id)

    async def test_delete_document_skips_storage_delete_when_object_missing(self) -> None:
        # Arrange
        service = _service()
        document = _document()
        service._documents_read.get_by_id.return_value = document
        service._storage_read.object_exists.return_value = False

        # Act
        await service.delete_document(document.id)

        # Assert
        service._job_service.cancel_indexing_for_document.assert_awaited_once_with(document.id)
        service._storage_write.delete.assert_not_called()
        service._documents_write.delete.assert_awaited_once_with(document.id)

    async def test_resolve_index_status_indexed(self) -> None:
        # Arrange
        service = _service()
        document = _document(indexed_at=datetime.now(UTC))

        # Act
        status = await service._resolve_index_status(document)

        # Assert
        self.assertEqual(status, IndexStatus.INDEXED)
        service._jobs_read.find_active_for_document.assert_not_awaited()

    async def test_resolve_index_status_indexing(self) -> None:
        # Arrange
        service = _service()
        document = _document()
        service._jobs_read.find_active_for_document.return_value = IndexJob(
            tenant_id="tenant-1",
            document_id=document.id,
            status=JobStatus.RUNNING,
        )

        # Act
        status = await service._resolve_index_status(document)

        # Assert
        self.assertEqual(status, IndexStatus.INDEXING)

    async def test_resolve_index_status_failed(self) -> None:
        # Arrange
        service = _service()
        document = _document()
        service._jobs_read.find_active_for_document.return_value = None
        service._jobs_read.get_latest_for_document.return_value = IndexJob(
            tenant_id="tenant-1",
            document_id=document.id,
            status=JobStatus.FAILED,
        )

        # Act
        status = await service._resolve_index_status(document)

        # Assert
        self.assertEqual(status, IndexStatus.FAILED)

    async def test_resolve_index_status_pending(self) -> None:
        # Arrange
        service = _service()
        document = _document()
        service._jobs_read.find_active_for_document.return_value = None
        service._jobs_read.get_latest_for_document.return_value = None

        # Act
        status = await service._resolve_index_status(document)

        # Assert
        self.assertEqual(status, IndexStatus.PENDING)


if __name__ == "__main__":
    unittest.main()
