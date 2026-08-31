import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from agentic_shared.integrations.litellm.core.settings import LiteLLMSettings
from agentic_shared.integrations.litellm.rerank.client import LiteLLMRerankClient
from agentic_shared.integrations.litellm.rerank.errors import RerankError
from agentic_shared.integrations.litellm.rerank.models import RerankResult
from agentic_shared.integrations.litellm.rerank.settings import LiteLLMRerankSettings


class TestRerankResult(unittest.TestCase):
    def test_from_litellm_results(self) -> None:
        result = RerankResult.from_api_response(
            {
                "results": [
                    {"index": 1, "relevance_score": 0.2},
                    {"index": 0, "relevance_score": 0.9},
                ]
            }
        )
        self.assertEqual([hit.index for hit in result.hits], [0, 1])
        self.assertEqual(result.hits[0].score, 0.9)

    def test_from_tei_list(self) -> None:
        result = RerankResult.from_api_response(
            [{"index": 2, "score": 0.1}, {"index": 0, "score": 0.8}]
        )
        self.assertEqual([hit.index for hit in result.hits], [0, 2])


class TestLiteLLMRerankClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.llm = LiteLLMSettings(
            litellm_base_url="http://litellm:4000/",
            litellm_master_key="sk-test",
            _env_file=None,
        )
        self.settings = LiteLLMRerankSettings(rerank_enabled=True, _env_file=None)

    @patch("agentic_shared.integrations.litellm.rerank.client.httpx.AsyncClient")
    async def test_rerank_posts_litellm_body(self, http_cls: MagicMock) -> None:
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"results": [{"index": 1, "relevance_score": 0.95}]}
        http = MagicMock()
        http.post = AsyncMock(return_value=response)
        http.aclose = AsyncMock()
        http_cls.return_value = http

        client = LiteLLMRerankClient(self.llm, self.settings)
        hits = await client.rerank("iban", ["gamma", "alpha"], top_n=1)

        self.assertEqual(hits[0].index, 1)
        self.assertEqual(http.post.await_args.args[0], "/rerank")
        self.assertEqual(
            http.post.await_args.kwargs["json"],
            {
                "model": "rerank",
                "query": "iban",
                "documents": ["gamma", "alpha"],
                "top_n": 1,
            },
        )
        await client.aclose()

    @patch("agentic_shared.integrations.litellm.rerank.client.httpx.AsyncClient")
    async def test_rerank_clips_long_documents(self, http_cls: MagicMock) -> None:
        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"results": [{"index": 0, "relevance_score": 0.5}]}
        http = MagicMock()
        http.post = AsyncMock(return_value=response)
        http.aclose = AsyncMock()
        http_cls.return_value = http

        client = LiteLLMRerankClient(
            self.llm,
            LiteLLMRerankSettings(rerank_enabled=True, rerank_max_doc_chars=8, _env_file=None),
        )
        await client.rerank("q", ["abcdefghij"], top_n=1)

        self.assertEqual(http.post.await_args.kwargs["json"]["documents"], ["abcdefgh"])
        await client.aclose()

    @patch("agentic_shared.integrations.litellm.rerank.client.httpx.AsyncClient")
    async def test_rerank_disabled_skips_http(self, http_cls: MagicMock) -> None:
        http = MagicMock()
        http.post = AsyncMock()
        http.aclose = AsyncMock()
        http_cls.return_value = http

        client = LiteLLMRerankClient(
            self.llm,
            LiteLLMRerankSettings(rerank_enabled=False, _env_file=None),
        )
        hits = await client.rerank("q", ["a"], top_n=1)

        self.assertEqual(hits, [])
        http.post.assert_not_called()
        await client.aclose()

    @patch("agentic_shared.integrations.litellm.rerank.client.httpx.AsyncClient")
    async def test_rerank_http_error(self, http_cls: MagicMock) -> None:
        import httpx

        http = MagicMock()
        http.post = AsyncMock(side_effect=httpx.ConnectError("down"))
        http.aclose = AsyncMock()
        http_cls.return_value = http

        client = LiteLLMRerankClient(self.llm, self.settings)
        with self.assertRaises(RerankError):
            await client.rerank("q", ["a", "b"], top_n=1)
        await client.aclose()


class TestLiteLLMRerankSettings(unittest.TestCase):
    def test_defaults(self) -> None:
        settings = LiteLLMRerankSettings(rerank_enabled=True, _env_file=None)
        self.assertEqual(settings.title, "litellm-rerank")
        self.assertTrue(settings.rerank_enabled)
        self.assertEqual(settings.rerank_model, "rerank")


if __name__ == "__main__":
    unittest.main()
