from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.domains.retrieval.service import AsyncRetrievalService, RetrievalService
from agentic_shared.infrastructure.vector.client import QdrantClient, QdrantVectorReader
from agentic_shared.infrastructure.vector.protocols import QdrantReader
from agentic_shared.infrastructure.vector.settings import QdrantSettings
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.client import RerankClient
from agentic_shared.integrations.rerank.settings import RerankSettings


def create_retrieval_service(
    *,
    qdrant: QdrantSettings,
    llm: LLMSettings,
    embedding: EmbeddingSettings,
    rerank: RerankSettings,
    qdrant_read: QdrantReader | None = None,
    rerank_client: RerankClient | None = None,
) -> RetrievalService:
    reader = qdrant_read or QdrantVectorReader(QdrantClient(qdrant))
    return RetrievalService(
        reader,
        llm,
        embedding,
        rerank,
        rerank_client=rerank_client,
    )


def create_async_retrieval_service(
    *,
    qdrant: QdrantSettings,
    llm: LLMSettings,
    embedding: EmbeddingSettings,
    rerank: RerankSettings,
    qdrant_read: QdrantReader | None = None,
    rerank_client: RerankClient | None = None,
) -> AsyncRetrievalReader:
    return AsyncRetrievalService(
        create_retrieval_service(
            qdrant=qdrant,
            llm=llm,
            embedding=embedding,
            rerank=rerank,
            qdrant_read=qdrant_read,
            rerank_client=rerank_client,
        )
    )
