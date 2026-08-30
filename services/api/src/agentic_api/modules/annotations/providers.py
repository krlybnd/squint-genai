from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.tenant import resolve_tenant_id
from agentic_shared.domains.annotations.protocols.comments import CommentWriteRepository
from agentic_shared.domains.retrieval.protocols.chunks import ChunkReadRepository
from agentic_shared.integrations.litellm.embedding.protocols import EmbeddingClient
from agentic_shared.integrations.litellm.guard.protocols import Guard
from agentic_shared.integrations.litellm.llm.protocols import ChatClient
from dishka import Provider, Scope, provide

from agentic_api.modules.annotations.deps import CommentGraphDeps
from agentic_api.modules.annotations.graph import build_comment_graph
from agentic_api.modules.annotations.service import AnnotationService
from agentic_api.modules.annotations.state import CommentCompiledGraph


class AnnotationsProvider(Provider):
    @provide(scope=Scope.APP)
    def comment_graph_deps(
        self,
        chat_client: ChatClient,
        embedding_client: EmbeddingClient,
        comment_write: CommentWriteRepository,
        guard: Guard,
    ) -> CommentGraphDeps:
        return CommentGraphDeps(
            chat_client=chat_client,
            embedding_client=embedding_client,
            comment_write=comment_write,
            guard=guard,
        )

    @provide(scope=Scope.APP)
    def comment_graph(self, deps: CommentGraphDeps) -> CommentCompiledGraph:
        return build_comment_graph(deps)

    @provide(scope=Scope.REQUEST)
    def annotation_service(
        self,
        auth: AuthContext,
        chunk_read: ChunkReadRepository,
        comment_graph: CommentCompiledGraph,
    ) -> AnnotationService:
        return AnnotationService(
            tenant_id=resolve_tenant_id(auth),
            chunk_read=chunk_read,
            graph=comment_graph,
        )
