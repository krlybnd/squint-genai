from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.infrastructure.storage.core.protocols import StorageReader, StorageWriter
from agentic_shared.infrastructure.storage.minio.client import MinioClient
from agentic_shared.infrastructure.storage.minio.reader import MinioStorageReader
from agentic_shared.infrastructure.storage.minio.settings import MinioSettings
from agentic_shared.infrastructure.storage.minio.writer import MinioStorageWriter


class MinioProvider(Provider):
    def __init__(self, settings: MinioSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def minio_client(self) -> AsyncIterator[MinioClient]:
        async with MinioClient(self._settings) as client:
            yield client

    @provide(scope=Scope.APP)
    def storage_reader(self, minio_client: MinioClient) -> StorageReader:
        return MinioStorageReader(minio_client)

    @provide(scope=Scope.APP)
    def storage_writer(self, minio_client: MinioClient) -> StorageWriter:
        return MinioStorageWriter(minio_client)
