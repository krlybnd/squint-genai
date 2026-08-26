"""Dishka IoC registry — provider implementations live in their owning modules."""

from agentic_shared.core.auth.providers import AuthProvider
from agentic_shared.core.health.providers import make_resource_health_provider
from agentic_shared.core.ioc.container import make_service_container
from agentic_shared.infrastructure.object_storage.protocols import ObjectStorageReader
from agentic_shared.infrastructure.object_storage.providers import StorageProvider
from agentic_shared.infrastructure.postgres.client import DatabaseClient
from agentic_shared.infrastructure.postgres.providers import DatabaseProvider
from agentic_shared.infrastructure.redis.protocols import RedisReader
from agentic_shared.infrastructure.redis.providers import RedisProvider
from agentic_shared.infrastructure.vector.protocols import QdrantReader
from agentic_shared.infrastructure.vector.providers import QdrantProvider
from agentic_shared.integrations.embedding.protocols import EmbeddingClient
from agentic_shared.integrations.embedding.providers import EmbeddingProvider
from agentic_shared.integrations.llm.protocols import ChatClient
from agentic_shared.integrations.llm.providers import LLMProvider

__all__ = [
    "AuthProvider",
    "DatabaseProvider",
    "EmbeddingProvider",
    "LLMProvider",
    "QdrantProvider",
    "RedisProvider",
    "StorageProvider",
    "infrastructure_health_provider",
    "make_service_container",
    "resource_health_provider",
]


def resource_health_provider():
    return make_resource_health_provider(
        DatabaseClient,
        QdrantReader,
        RedisReader,
        ObjectStorageReader,
        ChatClient,
        EmbeddingClient,
    )


infrastructure_health_provider = resource_health_provider
