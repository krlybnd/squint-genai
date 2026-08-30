from agentic_shared.core.resources.client import BaseResourceClient
from agentic_shared.infrastructure.core.settings import InfraSettings


class InfrastructureClient[S: InfraSettings](BaseResourceClient[S]):
    """Base client for infrastructure resources (Postgres, Redis, MinIO, Qdrant)."""


__all__ = ["InfrastructureClient"]
