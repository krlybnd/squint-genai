from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide

from agentic_shared.infrastructure.core.client import open_client
from agentic_shared.infrastructure.object_storage.client import (
    MinioClient,
    MinioObjectStorageReader,
    MinioObjectStorageWriter,
)
from agentic_shared.infrastructure.object_storage.protocols import (
    ObjectStorageReader,
    ObjectStorageWriter,
)
from agentic_shared.infrastructure.object_storage.settings import MinioSettings


class StorageProvider(Provider):
    def __init__(self, settings: MinioSettings) -> None:
        super().__init__()
        self._settings = settings

    @provide(scope=Scope.APP)
    async def minio_client(self) -> AsyncIterator[MinioClient]:
        async with open_client(MinioClient(self._settings)) as client:
            yield client

    @provide(scope=Scope.APP)
    def object_storage_reader(self, minio_client: MinioClient) -> ObjectStorageReader:
        return MinioObjectStorageReader(minio_client)

    @provide(scope=Scope.APP)
    def object_storage_writer(self, minio_client: MinioClient) -> ObjectStorageWriter:
        return MinioObjectStorageWriter(minio_client)
