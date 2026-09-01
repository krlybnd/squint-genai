from dataclasses import dataclass

from agentic_shared.crosscut.crypto.cipher import FernetCipher
from agentic_shared.crosscut.crypto.settings import CryptoSettings
from agentic_shared.domains.pii_vault.lookup import (
    SqlAlchemyVaultPersonIdentity,
    SqlAlchemyVaultTokenLookup,
)
from agentic_shared.domains.pii_vault.protocols import QueryPiiTokenizationPort
from agentic_shared.domains.pii_vault.query_service import QueryPiiTokenizationService
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.domains.pii_vault.tokenizer import PiiTokenizer
from agentic_shared.domains.retrieval.factory import create_async_retrieval_service
from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.domains.retrieval.repositories.qdrant_.chunks import QdrantChunkReadRepository
from agentic_shared.infrastructure.sql.core.session import create_session_factory
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings
from agentic_shared.infrastructure.vector.qdrant.client import QdrantClient
from agentic_shared.integrations.litellm.analyzer.client import AnalyzerClient
from agentic_shared.integrations.litellm.analyzer.protocols import Analyzer
from agentic_shared.integrations.litellm.anonymizer.client import AnonymizerClient
from agentic_shared.integrations.litellm.anonymizer.protocols import Anonymizer
from agentic_shared.integrations.litellm.guard.client import GuardClient
from agentic_shared.integrations.litellm.guard.protocols import Guard
from agentic_shared.integrations.litellm.llm import LiteLLMChatClient
from agentic_shared.integrations.litellm.llm.protocols import ChatClient
from agentic_shared.integrations.litellm.rerank.client import LiteLLMRerankClient

from agentic_chat.modules.chat.settings import get_module_settings as get_chat_module_settings
from agentic_chat.settings import load_settings


@dataclass(frozen=True, slots=True)
class AgentGraphDeps:
    chat_client: ChatClient
    retrieval: AsyncRetrievalReader
    qdrant_top_k: int
    guard: Guard
    analyzer: Analyzer
    anonymizer: Anonymizer
    query_pii: QueryPiiTokenizationPort
    pii_vault: PiiVaultSettings


def agent_graph_deps_from_settings() -> AgentGraphDeps:
    """Composition helper for tests and graph bootstrap without Dishka."""
    root = load_settings()
    chat_module = get_chat_module_settings()
    qdrant = QdrantClient(root.qdrant)
    crypto = CryptoSettings()
    pii_vault = PiiVaultSettings()
    existence = None
    person_identity = None
    if pii_vault.enabled:
        session_factory = create_session_factory(DatabaseSettings().database_url)
        existence = SqlAlchemyVaultTokenLookup(session_factory)
        person_identity = SqlAlchemyVaultPersonIdentity(session_factory, FernetCipher(crypto))
    query_pii = QueryPiiTokenizationService(
        analyzer=AnalyzerClient(root.analyzer),
        tokenizer=PiiTokenizer(token_salt=crypto.token_salt),
        settings=pii_vault,
        existence=existence,
        person_identity=person_identity,
    )
    return AgentGraphDeps(
        chat_client=LiteLLMChatClient(root.llm),
        retrieval=create_async_retrieval_service(
            chunk_read=QdrantChunkReadRepository(qdrant),
            llm=root.llm,
            embedding=root.embedding,
            query_pii=query_pii,
            reranker=LiteLLMRerankClient(root.llm, root.rerank),
        ),
        qdrant_top_k=chat_module.qdrant_top_k or root.qdrant.top_k,
        guard=GuardClient(root.guard),
        analyzer=AnalyzerClient(root.analyzer),
        anonymizer=AnonymizerClient(root.anonymizer),
        query_pii=query_pii,
        pii_vault=pii_vault,
    )
