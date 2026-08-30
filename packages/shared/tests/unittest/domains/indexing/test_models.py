import unittest
import uuid

from agentic_shared.domains.indexing.models import IndexDocumentTaskResult


class TestIndexDocumentTaskResult(unittest.TestCase):
    def test_from_run_and_celery_payload(self) -> None:
        document_id = uuid.uuid4()
        result = IndexDocumentTaskResult.from_run(document_id=document_id, chunk_count=3)
        self.assertEqual(result.document_id, str(document_id))
        self.assertEqual(result.chunk_count, 3)
        self.assertEqual(
            result.to_celery_result(),
            {"document_id": str(document_id), "chunk_count": 3},
        )
