import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.models import ChatCompletionResult
from agentic_shared.integrations.llm.settings import LLMSettings


class TestOpenAIChatClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = LLMSettings(
            litellm_base_url="http://llm:4000/",
            litellm_model="gpt-test",
            openai_api_key="sk-test",
        )

    def test_lazy_export_from_package(self) -> None:
        # Arrange / Act
        from agentic_shared.integrations import llm as llm_pkg

        # Assert
        self.assertEqual(llm_pkg.OpenAIChatClient.__name__, "OpenAIChatClient")

    @patch("agentic_shared.integrations.llm.openai.AsyncOpenAI")
    async def test_chat_completion_returns_parsed_result(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.llm.openai import OpenAIChatClient

        dumped = {"choices": [{"message": {"role": "assistant", "content": "hello"}}]}
        api_response = MagicMock()
        api_response.model_dump.return_value = dumped
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=api_response)
        client.close = AsyncMock()
        openai_cls.return_value = client
        chat = OpenAIChatClient(self.settings)

        # Act
        result = await chat.chat_completion([{"role": "user", "content": "hi"}])

        # Assert
        self.assertIsInstance(result, ChatCompletionResult)
        self.assertEqual(result.content, "hello")
        kwargs = client.chat.completions.create.await_args.kwargs
        self.assertEqual(kwargs["model"], "gpt-test")
        self.assertFalse(kwargs["stream"])
        await chat.aclose()
        client.close.assert_awaited_once()

    @patch("agentic_shared.integrations.llm.openai.AsyncOpenAI")
    async def test_streaming_returns_raw_response(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.llm.openai import OpenAIChatClient

        stream = object()
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=stream)
        openai_cls.return_value = client
        chat = OpenAIChatClient(self.settings)

        # Act / Assert
        self.assertIs(await chat.chat_completion([], stream=True), stream)

    @patch("agentic_shared.integrations.llm.openai.httpx.AsyncClient")
    @patch("agentic_shared.integrations.llm.openai.AsyncOpenAI")
    async def test_health_check_true_on_200(
        self, openai_cls: MagicMock, http_cls: MagicMock
    ) -> None:
        # Arrange
        from agentic_shared.integrations.llm.openai import OpenAIChatClient

        openai_cls.return_value = MagicMock()
        response = MagicMock(status_code=200)
        http = MagicMock()
        http.get = AsyncMock(return_value=response)
        http.__aenter__ = AsyncMock(return_value=http)
        http.__aexit__ = AsyncMock(return_value=None)
        http_cls.return_value = http
        chat = OpenAIChatClient(self.settings)

        # Act / Assert
        self.assertTrue(await chat.health_check())
        url = http.get.await_args.args[0]
        self.assertEqual(url, "http://llm:4000/health")

    @patch("agentic_shared.integrations.llm.openai.httpx.AsyncClient")
    @patch("agentic_shared.integrations.llm.openai.AsyncOpenAI")
    async def test_health_check_false_on_http_error(
        self, openai_cls: MagicMock, http_cls: MagicMock
    ) -> None:
        # Arrange
        import httpx

        from agentic_shared.integrations.llm.openai import OpenAIChatClient

        openai_cls.return_value = MagicMock()
        http = MagicMock()
        http.get = AsyncMock(side_effect=httpx.ConnectError("down"))
        http.__aenter__ = AsyncMock(return_value=http)
        http.__aexit__ = AsyncMock(return_value=None)
        http_cls.return_value = http

        # Act / Assert
        self.assertFalse(await OpenAIChatClient(self.settings).health_check())


class TestOpenAIEmbeddingClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.llm = LLMSettings(litellm_base_url="http://llm:4000", openai_api_key="sk-test")
        self.embedding = EmbeddingSettings(embedding_model="emb-test")

    def test_lazy_export_from_package(self) -> None:
        # Arrange / Act
        from agentic_shared.integrations import embedding as emb_pkg

        # Assert
        self.assertEqual(emb_pkg.OpenAIEmbeddingClient.__name__, "OpenAIEmbeddingClient")

    @patch("agentic_shared.integrations.embedding.openai.AsyncOpenAI")
    async def test_embed_returns_vectors(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.embedding.openai import OpenAIEmbeddingClient

        item = MagicMock()
        item.embedding = [0.1, 0.2]
        response = MagicMock(data=[item])
        client = MagicMock()
        client.embeddings.create = AsyncMock(return_value=response)
        client.close = AsyncMock()
        openai_cls.return_value = client
        embeddings = OpenAIEmbeddingClient(self.llm, self.embedding)

        # Act
        vectors = await embeddings.embed(["hello"])

        # Assert
        self.assertEqual(vectors, [[0.1, 0.2]])
        await embeddings.aclose()
        client.close.assert_awaited_once()

    @patch("agentic_shared.integrations.embedding.openai.AsyncOpenAI")
    async def test_health_check_lists_models(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.embedding.openai import OpenAIEmbeddingClient

        client = MagicMock()
        client.models.list = AsyncMock(return_value=MagicMock())
        openai_cls.return_value = client

        # Act / Assert
        self.assertTrue(await OpenAIEmbeddingClient(self.llm, self.embedding).health_check())

    @patch("agentic_shared.integrations.embedding.openai.AsyncOpenAI")
    async def test_health_check_false_on_error(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.embedding.openai import OpenAIEmbeddingClient

        client = MagicMock()
        client.models.list = AsyncMock(side_effect=RuntimeError("down"))
        openai_cls.return_value = client

        # Act / Assert
        self.assertFalse(await OpenAIEmbeddingClient(self.llm, self.embedding).health_check())


if __name__ == "__main__":
    unittest.main()
