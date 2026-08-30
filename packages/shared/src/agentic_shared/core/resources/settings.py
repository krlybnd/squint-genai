from pydantic import Field

from agentic_shared.core.settings.base import EnvSettings


class ResourceSettings(EnvSettings):
    """Marker base for infrastructure and integration client settings."""

    title: str = Field(
        default="resource",
        description="Stable client label used in open/close logs and readiness maps.",
    )
