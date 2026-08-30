import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.models import ChatCompletionResult
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings


class TestLiteLLMChatClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = LiteLLMChatSettings(
            litellm_base_url="http://llm:4000/",
            litellm_model="gpt-test",
            litellm_master_key="sk-test",
        )

    def test_lazy_export_from_package(self) -> None:
        # Arrange / Act
        from agentic_shared.integrations import litellm as litellm_pkg

        # Assert
        self.assertEqual(litellm_pkg.LiteLLMChatClient.__name__, "LiteLLMChatClient")

    @patch("agentic_shared.integrations.litellm.llm.client.AsyncOpenAI")
    async def test_chat_completion_returns_parsed_result(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.litellm.llm.client import LiteLLMChatClient

        dumped = {"choices": [{"message": {"role": "assistant", "content": "hello"}}]}
        api_response = MagicMock()
        api_response.model_dump.return_value = dumped
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=api_response)
        client.close = AsyncMock()
        openai_cls.return_value = client
        chat = LiteLLMChatClient(self.settings)

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

    @patch("agentic_shared.integrations.litellm.llm.client.AsyncOpenAI")
    async def test_chat_completion_model_override(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.litellm.llm.client import LiteLLMChatClient

        dumped = {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}
        api_response = MagicMock()
        api_response.model_dump.return_value = dumped
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=api_response)
        openai_cls.return_value = client
        chat = LiteLLMChatClient(self.settings)

        # Act
        await chat.chat_completion([{"role": "user", "content": "hi"}], model="router")

        # Assert
        kwargs = client.chat.completions.create.await_args.kwargs
        self.assertEqual(kwargs["model"], "router")

    @patch("agentic_shared.integrations.litellm.llm.client.AsyncOpenAI")
    async def test_stream_chat_completion_yields_delta_text(self, openai_cls: MagicMock) -> None:
        # Arrange
        from openai.types.chat import ChatCompletionChunk

        from agentic_shared.integrations.litellm.llm.client import LiteLLMChatClient

        def chunk(*, content: str | None = None, choices: bool = True) -> ChatCompletionChunk:
            payload: dict[str, object] = {
                "id": "chatcmpl-1",
                "created": 1,
                "model": "gpt-test",
                "object": "chat.completion.chunk",
                "choices": [],
            }
            if choices:
                delta: dict[str, str] = {} if content is None else {"content": content}
                payload["choices"] = [{"delta": delta, "index": 0}]
            return ChatCompletionChunk.model_validate(payload)

        async def events():
            yield chunk(content="hel")
            yield chunk(choices=False)
            yield chunk(content=None)
            yield chunk(content="lo")

        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=events())
        openai_cls.return_value = client
        chat = LiteLLMChatClient(self.settings)

        # Act
        pieces = [
            part async for part in chat.stream_chat_completion([{"role": "user", "content": "hi"}])
        ]

        # Assert
        self.assertEqual("".join(pieces), "hello")
        kwargs = client.chat.completions.create.await_args.kwargs
        self.assertTrue(kwargs["stream"])

    @patch("agentic_shared.integrations.litellm.llm.client.httpx.AsyncClient")
    @patch("agentic_shared.integrations.litellm.llm.client.AsyncOpenAI")
    async def test_health_check_true_on_200(
        self, openai_cls: MagicMock, http_cls: MagicMock
    ) -> None:
        # Arrange
        from agentic_shared.integrations.litellm.llm.client import LiteLLMChatClient

        openai_cls.return_value = MagicMock()
        response = MagicMock(status_code=200)
        http = MagicMock()
        http.get = AsyncMock(return_value=response)
        http.__aenter__ = AsyncMock(return_value=http)
        http.__aexit__ = AsyncMock(return_value=None)
        http_cls.return_value = http
        chat = LiteLLMChatClient(self.settings)

        # Act / Assert
        self.assertTrue(await chat.health_check())
        url = http.get.await_args.args[0]
        self.assertEqual(url, "http://llm:4000/health")

    @patch("agentic_shared.integrations.litellm.llm.client.httpx.AsyncClient")
    @patch("agentic_shared.integrations.litellm.llm.client.AsyncOpenAI")
    async def test_health_check_false_on_http_error(
        self, openai_cls: MagicMock, http_cls: MagicMock
    ) -> None:
        # Arrange
        import httpx

        from agentic_shared.integrations.litellm.llm.client import LiteLLMChatClient

        openai_cls.return_value = MagicMock()
        http = MagicMock()
        http.get = AsyncMock(side_effect=httpx.ConnectError("down"))
        http.__aenter__ = AsyncMock(return_value=http)
        http.__aexit__ = AsyncMock(return_value=None)
        http_cls.return_value = http

        # Act / Assert
        self.assertFalse(await LiteLLMChatClient(self.settings).health_check())


class TestLiteLLMEmbeddingClient(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.llm = LiteLLMChatSettings(
            litellm_base_url="http://llm:4000", litellm_master_key="sk-test"
        )
        self.embedding = LiteLLMEmbeddingSettings(embedding_model="emb-test")

    def test_lazy_export_from_package(self) -> None:
        # Arrange / Act
        from agentic_shared.integrations import litellm as litellm_pkg

        # Assert
        self.assertEqual(litellm_pkg.LiteLLMEmbeddingClient.__name__, "LiteLLMEmbeddingClient")

    @patch("agentic_shared.integrations.litellm.embedding.client.AsyncOpenAI")
    async def test_embed_returns_vectors(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.litellm.embedding.client import LiteLLMEmbeddingClient

        item = MagicMock()
        item.embedding = [0.1, 0.2]
        response = MagicMock(data=[item])
        client = MagicMock()
        client.embeddings.create = AsyncMock(return_value=response)
        client.close = AsyncMock()
        openai_cls.return_value = client
        embeddings = LiteLLMEmbeddingClient(self.llm, self.embedding)

        # Act
        vectors = await embeddings.embed(["hello"])

        # Assert
        self.assertEqual(vectors, [[0.1, 0.2]])
        await embeddings.aclose()
        client.close.assert_awaited_once()

    @patch("agentic_shared.integrations.litellm.embedding.client.AsyncOpenAI")
    async def test_health_check_lists_models(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.litellm.embedding.client import LiteLLMEmbeddingClient

        client = MagicMock()
        client.models.list = AsyncMock(return_value=MagicMock())
        openai_cls.return_value = client

        # Act / Assert
        self.assertTrue(await LiteLLMEmbeddingClient(self.llm, self.embedding).health_check())

    @patch("agentic_shared.integrations.litellm.embedding.client.AsyncOpenAI")
    async def test_health_check_false_on_error(self, openai_cls: MagicMock) -> None:
        # Arrange
        from agentic_shared.integrations.litellm.embedding.client import LiteLLMEmbeddingClient

        client = MagicMock()
        client.models.list = AsyncMock(side_effect=RuntimeError("down"))
        openai_cls.return_value = client

        # Act / Assert
        self.assertFalse(await LiteLLMEmbeddingClient(self.llm, self.embedding).health_check())


if __name__ == "__main__":
    unittest.main()
