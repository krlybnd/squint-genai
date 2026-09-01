from agentic_shared.domains.pii_vault.protocols import QueryPiiTokenizationPort
from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.domains.retrieval.protocols.chunks import ChunkReadRepository
from agentic_shared.domains.retrieval.service import AsyncRetrievalService, RetrievalService
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings
from agentic_shared.integrations.litellm.rerank.protocols import RerankPort


def create_retrieval_service(
    *,
    llm: LiteLLMChatSettings,
    embedding: LiteLLMEmbeddingSettings,
    chunk_read: ChunkReadRepository,
    query_pii: QueryPiiTokenizationPort | None = None,
    reranker: RerankPort | None = None,
) -> RetrievalService:
    return RetrievalService(chunk_read, llm, embedding, query_pii=query_pii, reranker=reranker)


def create_async_retrieval_service(
    *,
    llm: LiteLLMChatSettings,
    embedding: LiteLLMEmbeddingSettings,
    chunk_read: ChunkReadRepository,
    query_pii: QueryPiiTokenizationPort | None = None,
    reranker: RerankPort | None = None,
) -> AsyncRetrievalReader:
    return AsyncRetrievalService(
        create_retrieval_service(
            llm=llm,
            embedding=embedding,
            chunk_read=chunk_read,
            query_pii=query_pii,
            reranker=reranker,
        )
    )
