from agentic_shared.core.health.providers import make_resource_health_provider
from agentic_shared.infrastructure.cache.core.protocols import CacheReader
from agentic_shared.infrastructure.sql.postgres.client import DatabaseClient
from agentic_shared.infrastructure.storage.minio.client import MinioClient
from agentic_shared.infrastructure.vector.qdrant.client import QdrantClient
from agentic_shared.integrations.litellm.embedding.protocols import EmbeddingClient
from agentic_shared.integrations.litellm.llm.protocols import ChatClient
from dishka import Provider


def resource_health_provider() -> Provider:
    """Readiness checks for resources this API service actually wires."""
    return make_resource_health_provider(
        DatabaseClient,
        QdrantClient,
        CacheReader,
        MinioClient,
        ChatClient,
        EmbeddingClient,
    )
