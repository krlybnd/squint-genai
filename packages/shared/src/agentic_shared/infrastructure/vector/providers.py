from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.infrastructure.core.client import open_client
from agentic_shared.infrastructure.vector.client import (
    QdrantClient,
    QdrantVectorReader,
    QdrantVectorWriter,
)
from agentic_shared.infrastructure.vector.protocols import QdrantReader, QdrantWriter
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
    def qdrant_reader(self, qdrant_client: QdrantClient) -> QdrantReader:
        return QdrantVectorReader(qdrant_client)

    @provide(scope=Scope.APP)
    def qdrant_writer(self, qdrant_client: QdrantClient) -> QdrantWriter:
        return QdrantVectorWriter(qdrant_client)
