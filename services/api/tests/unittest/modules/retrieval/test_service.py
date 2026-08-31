import unittest
from unittest.mock import AsyncMock, patch

from agentic_shared.domains.pii_vault.settings import PiiVaultSettings

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

    async def test_source_file_chunks_reveals_vault_tokens(self) -> None:
        retrieval = AsyncMock()
        retrieval.list_source_file_chunks.return_value = [
            AsyncMock(
                chunk_id="c1",
                text="Ask <PERSON_AABBCCDD> today.",
                score=None,
                doc_id="d1",
                source_file="paper.pdf",
                page=1,
                comments=None,
            )
        ]
        vault = AsyncMock()
        vault.reveal_text.return_value = "Ask Jane VaultTest today."
        service = RetrievalApiService(
            retrieval,
            ApiSettings(),
            vault_reveal=vault,
            pii_vault=PiiVaultSettings(enabled=True, sse_detokenize_enabled=True, _env_file=None),
        )

        response = await service.source_file_chunks("paper.pdf", tenant_id="tenant-1")

        self.assertEqual(response.chunks[0].text, "Ask Jane VaultTest today.")
        vault.reveal_text.assert_awaited_with("Ask <PERSON_AABBCCDD> today.", marked=True)

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
