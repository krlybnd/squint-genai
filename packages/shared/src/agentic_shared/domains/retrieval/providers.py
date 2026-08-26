from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.domains.retrieval.factory import create_async_retrieval_service
from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.infrastructure.core.client import open_client
from agentic_shared.infrastructure.vector.client import QdrantClient, QdrantVectorReader
from agentic_shared.infrastructure.vector.settings import QdrantSettings
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.client import RerankClient
from agentic_shared.integrations.rerank.settings import RerankSettings


class AsyncRetrievalProvider(Provider):
    def __init__(
        self,
        qdrant: QdrantSettings,
        llm: LLMSettings,
        embedding: EmbeddingSettings,
        rerank: RerankSettings,
    ) -> None:
        super().__init__()
        self._qdrant = qdrant
        self._llm = llm
        self._embedding = embedding
        self._rerank = rerank

    @provide(scope=Scope.APP)
    async def async_retrieval_reader(self) -> AsyncIterator[AsyncRetrievalReader]:
        async with open_client(QdrantClient(self._qdrant)) as qdrant:
            async with open_client(RerankClient(self._llm, self._rerank)) as rerank:
                yield create_async_retrieval_service(
                    qdrant=self._qdrant,
                    llm=self._llm,
                    embedding=self._embedding,
                    rerank=self._rerank,
                    qdrant_read=QdrantVectorReader(qdrant),
                    rerank_client=rerank,
                )
