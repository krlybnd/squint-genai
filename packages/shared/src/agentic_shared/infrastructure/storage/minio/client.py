from minio import Minio
from minio.error import S3Error

from agentic_shared.infrastructure.core.client import InfrastructureClient
from agentic_shared.infrastructure.storage.minio.settings import MinioSettings


class MinioClient(InfrastructureClient[MinioSettings]):
    def __init__(self, settings: MinioSettings) -> None:
        super().__init__(settings)
        self._bucket = settings.minio_bucket
        self._sdk = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key.get_secret_value(),
            secret_key=settings.minio_secret_key.get_secret_value(),
            secure=settings.minio_secure,
        )
        self._bucket_ready = False

    async def health_check(self) -> bool:
        try:
            return self._sdk.bucket_exists(self._bucket)
        except Exception:
            self._logger.debug(
                "%s health check failed bucket=%s",
                self.title,
                self._bucket,
                exc_info=True,
            )
            return False

    def ensure_bucket(self) -> None:
        if self._bucket_ready:
            return
        if not self._sdk.bucket_exists(self._bucket):
            self._sdk.make_bucket(self._bucket)
            self._logger.info("created bucket=%s", self._bucket)
        self._bucket_ready = True

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def sdk(self) -> Minio:
        return self._sdk

    @property
    def settings(self) -> MinioSettings:
        return self._settings

    def object_exists(self, key: str) -> bool:
        try:
            self._sdk.stat_object(self._bucket, key)
            return True
        except S3Error:
            return False
