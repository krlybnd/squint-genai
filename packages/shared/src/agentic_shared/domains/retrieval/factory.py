from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.domains.retrieval.protocols.chunks import ChunkReadRepository
from agentic_shared.domains.retrieval.service import AsyncRetrievalService, RetrievalService
from agentic_shared.integrations.litellm.embedding.settings import LiteLLMEmbeddingSettings
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings


def create_retrieval_service(
    *,
    llm: LiteLLMChatSettings,
    embedding: LiteLLMEmbeddingSettings,
    chunk_read: ChunkReadRepository,
) -> RetrievalService:
    return RetrievalService(chunk_read, llm, embedding)


def create_async_retrieval_service(
    *,
    llm: LiteLLMChatSettings,
    embedding: LiteLLMEmbeddingSettings,
    chunk_read: ChunkReadRepository,
) -> AsyncRetrievalReader:
    return AsyncRetrievalService(
        create_retrieval_service(
            llm=llm,
            embedding=embedding,
            chunk_read=chunk_read,
        )
    )
