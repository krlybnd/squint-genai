from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.domains.pii_vault.query_service import QueryPiiTokenizationService
from agentic_shared.domains.retrieval.factory import create_async_retrieval_service
from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.domains.retrieval.protocols.chunks import ChunkReadRepository
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings


class AsyncRetrievalProvider(Provider):
    def __init__(
        self,
        llm: LiteLLMChatSettings,
        embedding: LiteLLMEmbeddingSettings,
    ) -> None:
        super().__init__()
        self._llm = llm
        self._embedding = embedding

    @provide(scope=Scope.APP)
    async def async_retrieval_reader(
        self,
        chunk_read: ChunkReadRepository,
        query_pii: QueryPiiTokenizationService,
    ) -> AsyncIterator[AsyncRetrievalReader]:
        yield create_async_retrieval_service(
            llm=self._llm,
            embedding=self._embedding,
            chunk_read=chunk_read,
            query_pii=query_pii,
        )
