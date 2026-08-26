import logging
from datetime import timedelta
from io import BytesIO
from urllib.parse import urlparse, urlunparse

from minio import Minio
from minio.error import S3Error

from agentic_shared.infrastructure.core.client import BaseInfraClient
from agentic_shared.infrastructure.object_storage.protocols import (
    ObjectStorageReader,
    ObjectStorageWriter,
)
from agentic_shared.infrastructure.object_storage.settings import MinioSettings

logger = logging.getLogger(__name__)


class MinioClient(BaseInfraClient[MinioSettings]):
    def __init__(self, settings: MinioSettings) -> None:
        super().__init__(settings)
        self._bucket = settings.minio_bucket
        self._sdk = self._build_sdk(settings.minio_endpoint)
        self._bucket_ready = False

    @staticmethod
    def _public_endpoint(settings: MinioSettings) -> str:
        return settings.minio_public_endpoint or settings.minio_endpoint

    def _build_sdk(self, endpoint: str) -> Minio:
        return Minio(
            endpoint,
            access_key=self._settings.minio_access_key,
            secret_key=self._settings.minio_secret_key,
            secure=self._settings.minio_secure,
        )

    async def health_check(self) -> bool:
        try:
            return self._sdk.bucket_exists(self._bucket)
        except Exception:
            logger.warning("minio health check failed bucket=%s", self._bucket, exc_info=True)
            return False

    def _ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        if not self._sdk.bucket_exists(self._bucket):
            self._sdk.make_bucket(self._bucket)
        self._bucket_ready = True

    def object_exists(self, key: str) -> bool:
        try:
            self._sdk.stat_object(self._bucket, key)
            return True
        except S3Error:
            return False

    def download(self, key: str) -> bytes:
        response = self._sdk.get_object(self._bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def upload(self, key: str, data: bytes, content_type: str = "application/pdf") -> str:
        self._ensure_bucket()
        self._sdk.put_object(
            self._bucket,
            key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return key

    def presigned_put_url(
        self,
        key: str,
        *,
        content_type: str = "application/pdf",
        expires_seconds: int | None = None,
    ) -> tuple[str, int]:
        self._ensure_bucket()
        expires = expires_seconds or self._settings.minio_presign_expiry_seconds
        internal_url = self._sdk.presigned_put_object(
            self._bucket,
            key,
            expires=timedelta(seconds=expires),
        )
        return self._rewrite_presigned_host(internal_url), expires

    def delete(self, key: str) -> None:
        self._sdk.remove_object(self._bucket, key)

    def _rewrite_presigned_host(self, url: str) -> str:
        public = self._public_endpoint(self._settings)
        internal = self._settings.minio_endpoint
        if public == internal:
            return url
        parsed = urlparse(url)
        public_parsed = urlparse(f"{'https' if self._settings.minio_secure else 'http'}://{public}")
        return urlunparse(parsed._replace(netloc=public_parsed.netloc, scheme=public_parsed.scheme))


class MinioObjectStorageReader(ObjectStorageReader):
    def __init__(self, client: MinioClient) -> None:
        self._client = client

    @property
    def title(self) -> str:
        return self._client.title

    async def health_check(self) -> bool:
        return await self._client.health_check()

    def object_exists(self, key: str) -> bool:
        return self._client.object_exists(key)

    def download(self, key: str) -> bytes:
        return self._client.download(key)


class MinioObjectStorageWriter(ObjectStorageWriter):
    def __init__(self, client: MinioClient) -> None:
        self._client = client

    def presigned_put_url(
        self,
        key: str,
        *,
        content_type: str = "application/pdf",
        expires_seconds: int | None = None,
    ) -> tuple[str, int]:
        return self._client.presigned_put_url(
            key,
            content_type=content_type,
            expires_seconds=expires_seconds,
        )

    def upload(self, key: str, data: bytes, content_type: str = "application/pdf") -> str:
        return self._client.upload(key, data, content_type=content_type)

    def delete(self, key: str) -> None:
        self._client.delete(key)
