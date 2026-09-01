from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.tenant import resolve_tenant_id
from agentic_shared.domains.persistence.protocols.chat import (
    ChatMessageReadRepository,
    ChatMessageWriteRepository,
    ChatSessionReadRepository,
    ChatSessionWriteRepository,
)
from agentic_shared.domains.pii_vault.query_service import QueryPiiTokenizationService
from agentic_shared.domains.pii_vault.reveal_service import VaultRevealService
from agentic_shared.domains.pii_vault.settings import PiiVaultSettings
from agentic_shared.domains.retrieval.protocols import AsyncRetrievalReader
from agentic_shared.integrations.litellm.analyzer.protocols import Analyzer
from agentic_shared.integrations.litellm.anonymizer.protocols import Anonymizer
from agentic_shared.integrations.litellm.guard.protocols import Guard
from agentic_shared.integrations.litellm.llm.protocols import ChatClient
from dishka import Provider, Scope, provide

from agentic_chat.core.deps import AgentGraphDeps
from agentic_chat.core.graph import build_graph, get_checkpointer
from agentic_chat.core.state import ChatCompiledGraph
from agentic_chat.modules.chat.service import ChatService
from agentic_chat.modules.chat.settings import get_module_settings as get_chat_module_settings
from agentic_chat.modules.chat.streaming.graph_runner import ChatGraphRunner
from agentic_chat.modules.chat.streaming.session_title import SessionTitleGenerator
from agentic_chat.modules.chat.streaming.stream_service import ChatStreamService
from agentic_chat.settings import ChatSettings


class ChatProvider(Provider):
    def __init__(self, settings: ChatSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    def agent_graph_deps(
        self,
        chat_client: ChatClient,
        retrieval: AsyncRetrievalReader,
        guard: Guard,
        analyzer: Analyzer,
        anonymizer: Anonymizer,
        query_pii: QueryPiiTokenizationService,
        pii_vault: PiiVaultSettings,
    ) -> AgentGraphDeps:
        chat_module = get_chat_module_settings()
        return AgentGraphDeps(
            chat_client=chat_client,
            retrieval=retrieval,
            qdrant_top_k=chat_module.qdrant_top_k or self._settings.qdrant.top_k,
            guard=guard,
            analyzer=analyzer,
            anonymizer=anonymizer,
            query_pii=query_pii,
            pii_vault=pii_vault,
        )

    @provide(scope=Scope.APP)
    async def chat_graph(self, deps: AgentGraphDeps) -> ChatCompiledGraph:
        checkpointer = await get_checkpointer(self._settings.database)
        return build_graph(checkpointer, deps=deps)

    @provide(scope=Scope.APP)
    def session_title_generator(self, chat_client: ChatClient) -> SessionTitleGenerator:
        return SessionTitleGenerator(chat_client)

    @provide(scope=Scope.REQUEST)
    def chat_graph_runner(
        self,
        chat_graph: ChatCompiledGraph,
        messages_write: ChatMessageWriteRepository,
        vault_reveal: VaultRevealService,
        pii_vault: PiiVaultSettings,
    ) -> ChatGraphRunner:
        return ChatGraphRunner(
            chat_graph,
            messages_write,
            vault_reveal=vault_reveal,
            pii_vault=pii_vault,
        )

    @provide(scope=Scope.REQUEST)
    def chat_service(
        self,
        sessions_read: ChatSessionReadRepository,
        sessions_write: ChatSessionWriteRepository,
        messages_read: ChatMessageReadRepository,
        messages_write: ChatMessageWriteRepository,
    ) -> ChatService:
        return ChatService(
            sessions_read,
            sessions_write,
            messages_read,
            messages_write,
        )

    @provide(scope=Scope.REQUEST)
    def chat_stream_service(
        self,
        auth: AuthContext,
        sessions_read: ChatSessionReadRepository,
        sessions_write: ChatSessionWriteRepository,
        messages_read: ChatMessageReadRepository,
        messages_write: ChatMessageWriteRepository,
        graph_runner: ChatGraphRunner,
        title_generator: SessionTitleGenerator,
        query_pii: QueryPiiTokenizationService,
        vault_reveal: VaultRevealService,
        analyzer: Analyzer,
        anonymizer: Anonymizer,
    ) -> ChatStreamService:
        return ChatStreamService(
            sessions_read,
            sessions_write,
            messages_read,
            messages_write,
            graph_runner,
            title_generator,
            tenant_id=resolve_tenant_id(auth),
            query_pii=query_pii,
            vault_reveal=vault_reveal,
            analyzer=analyzer,
            anonymizer=anonymizer,
        )
