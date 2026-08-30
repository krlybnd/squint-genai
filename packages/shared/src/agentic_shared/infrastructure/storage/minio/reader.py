from __future__ import annotations

from agentic_shared.infrastructure.storage.minio.client import MinioClient


class MinioStorageReader:
    def __init__(self, client: MinioClient) -> None:
        self._client = client

    def object_exists(self, key: str) -> bool:
        return self._client.object_exists(key)

    def download(self, key: str) -> bytes:
        response = self._client.sdk.get_object(self._client.bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
