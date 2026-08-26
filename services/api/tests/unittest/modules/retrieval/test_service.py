import unittest
from unittest.mock import AsyncMock, patch

from agentic_api.modules.retrieval.service import RetrievalApiService
from agentic_api.modules.retrieval.settings import RetrievalModuleSettings
from agentic_api.settings import ApiSettings


class TestRetrievalApiService(unittest.IsolatedAsyncioTestCase):
    async def test_search_uses_explicit_top_k(self) -> None:
        # Arrange
        retrieval = AsyncMock()
        retrieval.search_documents.return_value = []
        settings = ApiSettings()
        service = RetrievalApiService(retrieval, settings)

        # Act
        await service.search("query", top_k=7, tenant_id="tenant-1")

        # Assert
        retrieval.search_documents.assert_awaited_once_with(
            "query",
            top_k=7,
            tenant_id="tenant-1",
        )

    @patch("agentic_api.modules.retrieval.service.get_module_settings")
    async def test_search_falls_back_to_module_default_top_k(
        self, mock_get_module_settings: AsyncMock
    ) -> None:
        # Arrange
        mock_get_module_settings.return_value = RetrievalModuleSettings(default_top_k=9)
        retrieval = AsyncMock()
        retrieval.search_documents.return_value = []
        service = RetrievalApiService(retrieval, ApiSettings())

        # Act
        await service.search("query", top_k=None, tenant_id="tenant-1")

        # Assert
        retrieval.search_documents.assert_awaited_once_with(
            "query",
            top_k=9,
            tenant_id="tenant-1",
        )

    @patch("agentic_api.modules.retrieval.service.get_module_settings")
    async def test_search_falls_back_to_qdrant_settings_top_k(
        self, mock_get_module_settings: AsyncMock
    ) -> None:
        # Arrange
        mock_get_module_settings.return_value = RetrievalModuleSettings(default_top_k=None)
        retrieval = AsyncMock()
        retrieval.search_documents.return_value = []
        settings = ApiSettings()
        settings.qdrant.top_k = 11
        service = RetrievalApiService(retrieval, settings)

        # Act
        await service.search("query", top_k=None, tenant_id="tenant-1")

        # Assert
        retrieval.search_documents.assert_awaited_once_with(
            "query",
            top_k=11,
            tenant_id="tenant-1",
        )

    async def test_document_chunks_empty_defaults(self) -> None:
        # Arrange
        retrieval = AsyncMock()
        retrieval.list_document_chunks.return_value = []
        service = RetrievalApiService(retrieval, ApiSettings())

        # Act
        response = await service.document_chunks("doc-1", tenant_id="tenant-1")

        # Assert
        self.assertEqual(response.doc_id, "doc-1")
        self.assertIsNone(response.source_file)
        self.assertEqual(response.chunks, [])

    async def test_source_file_chunks_empty_defaults(self) -> None:
        # Arrange
        retrieval = AsyncMock()
        retrieval.list_source_file_chunks.return_value = []
        service = RetrievalApiService(retrieval, ApiSettings())

        # Act
        response = await service.source_file_chunks("paper.pdf", tenant_id="tenant-1")

        # Assert
        self.assertEqual(response.doc_id, "paper.pdf")
        self.assertEqual(response.source_file, "paper.pdf")
        self.assertEqual(response.chunks, [])


if __name__ == "__main__":
    unittest.main()
