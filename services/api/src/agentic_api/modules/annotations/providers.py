from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.tenant import resolve_tenant_id
from agentic_shared.infrastructure.vector.protocols import QdrantReader, QdrantWriter
from agentic_shared.integrations.embedding.protocols import EmbeddingClient
from agentic_shared.integrations.llm.protocols import ChatClient
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
        qdrant_read: QdrantReader,
        qdrant_writer: QdrantWriter,
    ) -> CommentGraphDeps:
        return CommentGraphDeps(
            chat_client=chat_client,
            embedding_client=embedding_client,
            qdrant_read=qdrant_read,
            qdrant_write=qdrant_writer,
        )

    @provide(scope=Scope.APP)
    def comment_graph(self, deps: CommentGraphDeps) -> CommentCompiledGraph:
        return build_comment_graph(deps)

    @provide(scope=Scope.REQUEST)
    def annotation_service(
        self,
        auth: AuthContext,
        qdrant_read: QdrantReader,
        comment_graph: CommentCompiledGraph,
    ) -> AnnotationService:
        return AnnotationService(
            tenant_id=resolve_tenant_id(auth),
            qdrant_read=qdrant_read,
            graph=comment_graph,
        )
