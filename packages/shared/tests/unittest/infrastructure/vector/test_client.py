import unittest
from unittest.mock import MagicMock

from agentic_shared.infrastructure.vector.client import QdrantClient
from agentic_shared.infrastructure.vector.settings import QdrantSettings


class TestQdrantClientDeleteDocumentVectors(unittest.TestCase):
    def test_delete_document_vectors_uses_tenant_and_doc_filter(self) -> None:
        # Arrange
        settings = QdrantSettings(qdrant_url="http://localhost:6333")
        client = QdrantClient(settings)
        sdk = MagicMock()
        client._sdk = sdk

        # Act
        client.delete_document_vectors("doc-1", tenant_id="tenant-a")

        # Assert
        sdk.delete.assert_called_once()
        call_kwargs = sdk.delete.call_args.kwargs
        self.assertEqual(call_kwargs["collection_name"], settings.qdrant_collection)
        selector = call_kwargs["points_selector"]
        self.assertIsNotNone(selector.filter)


if __name__ == "__main__":
    unittest.main()
