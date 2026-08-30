from __future__ import annotations

from datetime import timedelta
from io import BytesIO
from urllib.parse import urlparse, urlunparse

from agentic_shared.infrastructure.storage.minio.client import MinioClient


class MinioStorageWriter:
    def __init__(self, client: MinioClient) -> None:
        self._client = client

    def presigned_put_url(
        self,
        key: str,
        *,
        content_type: str = "application/pdf",
        expires_seconds: int | None = None,
    ) -> tuple[str, int]:
        self._client.ensure_bucket()
        settings = self._client.settings
        expires = expires_seconds or settings.minio_presign_expiry_seconds
        internal_url = self._client.sdk.presigned_put_object(
            self._client.bucket,
            key,
            expires=timedelta(seconds=expires),
        )
        return self._rewrite_presigned_host(internal_url), expires

    def upload(self, key: str, data: bytes, content_type: str = "application/pdf") -> str:
        self._client.ensure_bucket()
        self._client.sdk.put_object(
            self._client.bucket,
            key,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return key

    def delete(self, key: str) -> None:
        self._client.sdk.remove_object(self._client.bucket, key)

    def _rewrite_presigned_host(self, url: str) -> str:
        settings = self._client.settings
        public = settings.minio_public_endpoint or settings.minio_endpoint
        if public == settings.minio_endpoint:
            return url
        parsed = urlparse(url)
        public_parsed = urlparse(f"{'https' if settings.minio_secure else 'http'}://{public}")
        return urlunparse(parsed._replace(netloc=public_parsed.netloc, scheme=public_parsed.scheme))
