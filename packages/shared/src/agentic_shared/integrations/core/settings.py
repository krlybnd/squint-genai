from pydantic import Field

from agentic_shared.core.resources.settings import ResourceSettings


class IntegrationSettings(ResourceSettings):
    """Base settings for integration clients (LLM, embedding, IdP, …)."""

    title: str = Field(
        default="integration",
        description="Default title for integration clients; subclasses override per provider.",
    )
