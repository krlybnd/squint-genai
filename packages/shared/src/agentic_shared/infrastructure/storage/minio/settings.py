from pydantic import Field

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.infrastructure.core.settings import InfraSettings


class MinioSettings(InfraSettings):
    """MinIO / S3-compatible object storage for document blobs."""

    title: str = Field(default="minio", description="Readiness/log label for the MinIO client.")
    minio_endpoint: str = Field(
        default="localhost:9000",
        description="Host:port used by server-side SDK calls (no scheme).",
    )
    minio_public_endpoint: str | None = Field(
        default=None,
        description=(
            "Optional host:port embedded in browser-facing presigned URLs. "
            "When unset, minio_endpoint is used."
        ),
    )
    minio_access_key: SecuredStr = Field(
        default=SecuredStr("minioadmin"),
        description="S3 access key id for the MinIO account.",
    )
    minio_secret_key: SecuredStr = Field(
        default=SecuredStr("minioadmin"),
        description="S3 secret access key for the MinIO account.",
    )
    minio_bucket: str = Field(
        default="documents",
        description="Default bucket for uploaded documents.",
    )
    minio_secure: bool = Field(
        default=False,
        description="Use HTTPS when talking to MinIO (True in TLS-terminated deployments).",
    )
    minio_presign_expiry_seconds: int = Field(
        default=3600,
        description="Lifetime of presigned PUT/GET URLs in seconds.",
    )
