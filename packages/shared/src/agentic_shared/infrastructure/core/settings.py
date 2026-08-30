from pydantic import Field

from agentic_shared.core.resources.settings import ResourceSettings


class InfraSettings(ResourceSettings):
    """Base settings for infrastructure clients (Postgres, Redis, MinIO, Qdrant)."""

    title: str = Field(
        default="infrastructure",
        description="Default title for infra clients; subclasses override per engine.",
    )
