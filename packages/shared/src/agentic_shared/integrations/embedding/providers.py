from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.core.resources.client import open_resource
from agentic_shared.integrations.embedding.openai import OpenAIEmbeddingClient
from agentic_shared.integrations.embedding.protocols import EmbeddingClient
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings


class EmbeddingProvider(Provider):
    def __init__(self, llm: LLMSettings, embedding: EmbeddingSettings) -> None:
        super().__init__()
        self._llm = llm
        self._embedding = embedding

    @provide(scope=Scope.APP)
    async def embedding_client(self) -> AsyncIterator[EmbeddingClient]:
        async with open_resource(OpenAIEmbeddingClient(self._llm, self._embedding)) as client:
            yield client
