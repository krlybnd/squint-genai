from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.integrations.litellm.embedding.client import LiteLLMEmbeddingClient
from agentic_shared.integrations.litellm.embedding.protocols import EmbeddingClient
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings


class EmbeddingProvider(Provider):
    def __init__(self, llm: LiteLLMChatSettings, embedding: LiteLLMEmbeddingSettings) -> None:
        super().__init__()
        self._llm = llm
        self._embedding = embedding

    @provide(scope=Scope.APP)
    async def embedding_client(self) -> AsyncIterator[EmbeddingClient]:
        async with LiteLLMEmbeddingClient(self._llm, self._embedding) as client:
            yield client
