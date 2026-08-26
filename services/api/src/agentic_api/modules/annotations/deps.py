from dataclasses import dataclass

from agentic_shared.infrastructure.vector.protocols import QdrantReader, QdrantWriter
from agentic_shared.integrations.embedding.protocols import EmbeddingClient
from agentic_shared.integrations.llm.protocols import ChatClient


@dataclass(frozen=True, slots=True)
class CommentGraphDeps:
    chat_client: ChatClient
    embedding_client: EmbeddingClient
    qdrant_read: QdrantReader
    qdrant_write: QdrantWriter
