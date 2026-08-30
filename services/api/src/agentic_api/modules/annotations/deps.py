from dataclasses import dataclass

from agentic_shared.domains.annotations.protocols.comments import CommentWriteRepository
from agentic_shared.integrations.litellm.embedding.protocols import EmbeddingClient
from agentic_shared.integrations.litellm.guard.protocols import Guard
from agentic_shared.integrations.litellm.llm.protocols import ChatClient


@dataclass(frozen=True, slots=True)
class CommentGraphDeps:
    chat_client: ChatClient
    embedding_client: EmbeddingClient
    comment_write: CommentWriteRepository
    guard: Guard
