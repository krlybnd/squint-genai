from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.domains.annotations.protocols.comments import CommentWriteRepository
from agentic_shared.domains.annotations.repositories.qdrant_.comments import (
    QdrantCommentWriteRepository,
)
from agentic_shared.domains.retrieval.protocols.chunks import (
    ChunkReadRepository,
    ChunkWriteRepository,
)
from agentic_shared.domains.retrieval.repositories.qdrant_.chunks import (
    QdrantChunkReadRepository,
    QdrantChunkWriteRepository,
)
from agentic_shared.infrastructure.core.client import open_client
from agentic_shared.infrastructure.vector.client import QdrantClient
from agentic_shared.infrastructure.vector.settings import QdrantSettings


class QdrantProvider(Provider):
    def __init__(self, settings: QdrantSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def qdrant_client(self) -> AsyncIterator[QdrantClient]:
        async with open_client(QdrantClient(self._settings)) as client:
            yield client

    @provide(scope=Scope.APP)
    def chunk_read_repository(self, qdrant_client: QdrantClient) -> ChunkReadRepository:
        return QdrantChunkReadRepository(qdrant_client)

    @provide(scope=Scope.APP)
    def chunk_write_repository(self, qdrant_client: QdrantClient) -> ChunkWriteRepository:
        return QdrantChunkWriteRepository(qdrant_client)

    @provide(scope=Scope.APP)
    def comment_write_repository(self, qdrant_client: QdrantClient) -> CommentWriteRepository:
        return QdrantCommentWriteRepository(qdrant_client)
