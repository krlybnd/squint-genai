from agentic_shared.infrastructure.core.settings import InfraSettings


class MinioSettings(InfraSettings):
    title: str = "minio"
    minio_endpoint: str = "localhost:9000"
    minio_public_endpoint: str | None = None
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "documents"
    minio_secure: bool = False
    minio_presign_expiry_seconds: int = 3600
