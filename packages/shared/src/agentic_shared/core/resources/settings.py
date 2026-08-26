from agentic_shared.core.settings.base import EnvSettings


class ResourceSettings(EnvSettings):
    """Base settings for shared clients — each layer defines `title`."""

    title: str
