import unittest
import uuid
from unittest.mock import MagicMock, patch

from agentic_shared.domains.indexing.models import IndexDocumentTaskResult
from agentic_shared.domains.persistence.entities import JobStatus
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings

from agentic_indexing.core.indexing_document import IndexDocumentUseCase


class TestIndexDocumentUseCase(unittest.TestCase):
    def _make_use_case(
        self,
    ) -> tuple[IndexDocumentUseCase, MagicMock, MagicMock, MagicMock, MagicMock]:
        jobs = MagicMock()
        documents = MagicMock()
        storage_read = MagicMock()
        qdrant_write = MagicMock()
        use_case = IndexDocumentUseCase(
            jobs=jobs,
            documents=documents,
            storage_read=storage_read,
            qdrant_write=qdrant_write,
            llm=LLMSettings(),
            embedding=EmbeddingSettings(),
        )
        return use_case, jobs, documents, storage_read, qdrant_write

    @patch("agentic_indexing.core.indexing_document.index_pdf_bytes", return_value=3)
    def test_run_marks_running_updates_document_and_completes(
        self, mock_index_pdf_bytes: MagicMock
    ) -> None:
        # Arrange
        use_case, jobs, documents, storage_read, qdrant_write = self._make_use_case()
        job_id = uuid.uuid4()
        document_id = uuid.uuid4()
        storage_read.download.return_value = b"pdf-bytes"
        document = MagicMock()
        documents.get_by_id.return_value = document

        # Act
        result = use_case.run(
            job_id=job_id,
            document_id=document_id,
            minio_key="docs/key.pdf",
            filename="key.pdf",
            tenant_id="acme",
            mark_running=True,
        )

        # Assert
        jobs.update_status.assert_any_call(job_id, JobStatus.RUNNING)
        jobs.update_status.assert_any_call(job_id, JobStatus.COMPLETED)
        storage_read.download.assert_called_once_with("docs/key.pdf")
        mock_index_pdf_bytes.assert_called_once_with(
            b"pdf-bytes",
            doc_id=str(document_id),
            source_file="key.pdf",
            tenant_id="acme",
            qdrant_write=qdrant_write,
            llm=use_case._llm,
            embedding=use_case._embedding,
        )
        documents.update.assert_called_once_with(document)
        self.assertIsNotNone(document.indexed_at)
        self.assertEqual(
            result,
            IndexDocumentTaskResult.from_run(document_id=document_id, chunk_count=3),
        )

    @patch("agentic_indexing.core.indexing_document.index_pdf_bytes", return_value=0)
    def test_run_skips_running_status_when_mark_running_false(
        self, _mock_index_pdf_bytes: MagicMock
    ) -> None:
        # Arrange
        use_case, jobs, documents, storage_read, _qdrant_write = self._make_use_case()
        job_id = uuid.uuid4()
        document_id = uuid.uuid4()
        storage_read.download.return_value = b"pdf-bytes"
        documents.get_by_id.return_value = None

        # Act
        result = use_case.run(
            job_id=job_id,
            document_id=document_id,
            minio_key="docs/key.pdf",
            filename="key.pdf",
            tenant_id="default",
            mark_running=False,
        )

        # Assert
        running_calls = [
            call
            for call in jobs.update_status.call_args_list
            if call.args == (job_id, JobStatus.RUNNING)
        ]
        self.assertEqual(running_calls, [])
        jobs.update_status.assert_called_once_with(job_id, JobStatus.COMPLETED)
        documents.update.assert_not_called()
        self.assertEqual(
            result,
            IndexDocumentTaskResult.from_run(document_id=document_id, chunk_count=0),
        )


if __name__ == "__main__":
    unittest.main()
