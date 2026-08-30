import unittest
from unittest.mock import MagicMock

from agentic_shared.domains.retrieval.repositories.qdrant_.chunks import QdrantChunkWriteRepository
from agentic_shared.infrastructure.vector.core.types import VectorPayload
from agentic_shared.infrastructure.vector.qdrant.client import QdrantClient
from agentic_shared.infrastructure.vector.qdrant.reader import QdrantVectorReader
from agentic_shared.infrastructure.vector.qdrant.settings import QdrantSettings


class TestQdrantVectorReader(unittest.TestCase):
    def test_get_by_id_rejects_tenant_mismatch(self) -> None:
        # Arrange
        client = MagicMock()
        client.collection_name = "test"
        client._sdk.retrieve.return_value = [
            MagicMock(payload={"tenant_id": "other", "text": "hello"})
        ]
        repo = QdrantVectorReader[VectorPayload](client, VectorPayload)

        # Act
        payload = repo.get_by_id("point-1", tenant_id="tenant-a")

        # Assert
        self.assertIsNone(payload)

    def test_get_by_id_returns_validated_payload(self) -> None:
        # Arrange
        client = MagicMock()
        client.collection_name = "test"
        client._sdk.retrieve.return_value = [
            MagicMock(payload={"tenant_id": "tenant-a", "text": "hello"})
        ]
        repo = QdrantVectorReader[VectorPayload](client, VectorPayload)

        # Act
        payload = repo.get_by_id("point-1", tenant_id="tenant-a")

        # Assert
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.text, "hello")


class TestQdrantChunkWriteRepository(unittest.TestCase):
    def test_delete_by_doc_id_uses_tenant_and_doc_filter(self) -> None:
        # Arrange
        settings = QdrantSettings(qdrant_url="http://localhost:6333")
        client = QdrantClient(settings)
        sdk = MagicMock()
        client._sdk = sdk
        repo = QdrantChunkWriteRepository(client)

        # Act
        repo.delete_by_doc_id("doc-1", tenant_id="tenant-a")

        # Assert
        sdk.delete.assert_called_once()
        call_kwargs = sdk.delete.call_args.kwargs
        self.assertEqual(call_kwargs["collection_name"], settings.qdrant_collection)
        selector = call_kwargs["points_selector"]
        self.assertIsNotNone(selector.filter)


if __name__ == "__main__":
    unittest.main()
