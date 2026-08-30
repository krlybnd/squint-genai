from dataclasses import dataclass

from agentic_shared.domains.retrieval.factory import create_async_retrieval_service
from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.domains.retrieval.repositories.qdrant_.chunks import QdrantChunkReadRepository
from agentic_shared.infrastructure.vector.qdrant.client import QdrantClient
from agentic_shared.integrations.litellm.llm import LiteLLMChatClient
from agentic_shared.integrations.litellm.llm.protocols import ChatClient

from agentic_chat.modules.chat.settings import get_module_settings as get_chat_module_settings
from agentic_chat.settings import load_settings


@dataclass(frozen=True, slots=True)
class AgentGraphDeps:
    chat_client: ChatClient
    retrieval: AsyncRetrievalReader
    qdrant_top_k: int


def agent_graph_deps_from_settings() -> AgentGraphDeps:
    """Composition helper for tests and graph bootstrap without Dishka."""
    root = load_settings()
    chat_module = get_chat_module_settings()
    qdrant = QdrantClient(root.qdrant)
    return AgentGraphDeps(
        chat_client=LiteLLMChatClient(root.llm),
        retrieval=create_async_retrieval_service(
            chunk_read=QdrantChunkReadRepository(qdrant),
            llm=root.llm,
            embedding=root.embedding,
        ),
        qdrant_top_k=chat_module.qdrant_top_k or root.qdrant.top_k,
    )
