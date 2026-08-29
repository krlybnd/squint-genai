from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.domains.retrieval.protocols.chunks import ChunkReadRepository
from agentic_shared.domains.retrieval.service import AsyncRetrievalService, RetrievalService
from agentic_shared.integrations.embedding.settings import EmbeddingSettings
from agentic_shared.integrations.llm.settings import LLMSettings
from agentic_shared.integrations.rerank.client import RerankClient
from agentic_shared.integrations.rerank.settings import RerankSettings


def create_retrieval_service(
    *,
    llm: LLMSettings,
    embedding: EmbeddingSettings,
    rerank: RerankSettings,
    chunk_read: ChunkReadRepository,
    rerank_client: RerankClient | None = None,
) -> RetrievalService:
    return RetrievalService(
        chunk_read,
        llm,
        embedding,
        rerank,
        rerank_client=rerank_client,
    )


def create_async_retrieval_service(
    *,
    llm: LLMSettings,
    embedding: EmbeddingSettings,
    rerank: RerankSettings,
    chunk_read: ChunkReadRepository,
    rerank_client: RerankClient | None = None,
) -> AsyncRetrievalReader:
    return AsyncRetrievalService(
        create_retrieval_service(
            llm=llm,
            embedding=embedding,
            rerank=rerank,
            chunk_read=chunk_read,
            rerank_client=rerank_client,
        )
    )
