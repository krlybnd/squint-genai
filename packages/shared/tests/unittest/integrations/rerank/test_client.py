import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.client import RerankClient
from agentic_shared.integrations.rerank.settings import RerankSettings


class TestRerankClient(unittest.TestCase):
    def test_rerank_client_returns_indices_in_provider_order(self) -> None:
        # Arrange
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {
            "results": [{"index": 1, "relevance_score": 0.9}, {"index": 0, "relevance_score": 0.5}]
        }
        client = RerankClient(
            LLMSettings(),
            RerankSettings(rerank_enabled=True, cohere_api_key="test-key"),
        )

        # Act / Assert
        with patch("httpx.Client.post", return_value=response):
            self.assertEqual(client.rerank("query", ["first", "second"], top_n=2), [1, 0])

    def test_rerank_disabled_returns_identity_indices(self) -> None:
        # Arrange
        client = RerankClient(LLMSettings(), RerankSettings(rerank_enabled=False))

        # Act / Assert
        self.assertEqual(client.rerank("query", ["a", "b", "c"], top_n=2), [0, 1])

    def test_rerank_empty_documents_returns_empty_list(self) -> None:
        # Arrange
        client = RerankClient(
            LLMSettings(),
            RerankSettings(rerank_enabled=True, cohere_api_key="test-key"),
        )

        # Act / Assert
        self.assertEqual(client.rerank("query", [], top_n=5), [])

    def test_rerank_single_document_skips_http(self) -> None:
        # Arrange
        client = RerankClient(
            LLMSettings(),
            RerankSettings(rerank_enabled=True, cohere_api_key="test-key"),
        )

        # Act / Assert
        with patch("httpx.Client.post") as mock_post:
            self.assertEqual(client.rerank("query", ["only"], top_n=1), [0])
            mock_post.assert_not_called()

    def test_rerank_empty_results_falls_back_to_identity(self) -> None:
        # Arrange
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"results": []}
        client = RerankClient(
            LLMSettings(),
            RerankSettings(rerank_enabled=True, cohere_api_key="test-key"),
        )

        # Act / Assert
        with patch("httpx.Client.post", return_value=response):
            self.assertEqual(client.rerank("query", ["a", "b"], top_n=2), [0, 1])


class TestRerankClientAsync(unittest.IsolatedAsyncioTestCase):
    async def test_rerank_client_async_returns_indices_in_provider_order(self) -> None:
        # Arrange
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {
            "results": [{"index": 1, "relevance_score": 0.9}, {"index": 0, "relevance_score": 0.5}]
        }
        client = RerankClient(
            LLMSettings(),
            RerankSettings(rerank_enabled=True, cohere_api_key="test-key"),
        )

        # Act / Assert
        with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=response)):
            result = await client.rerank_async("query", ["first", "second"], top_n=2)
            self.assertEqual(result, [1, 0])

    async def test_rerank_client_health_check_when_disabled(self) -> None:
        # Arrange
        client = RerankClient(LLMSettings(), RerankSettings(rerank_enabled=False))

        # Act / Assert
        self.assertTrue(await client.health_check())


if __name__ == "__main__":
    unittest.main()
