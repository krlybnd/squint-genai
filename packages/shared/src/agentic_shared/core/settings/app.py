from pydantic import Field

from agentic_shared.core.settings.base import EnvSettings


class AppSettings(EnvSettings):
    """Base for service-level composed settings (api, chat, admin, indexing)."""

    log_level: str = Field(
        default="INFO",
        description="Root log level for the service process (DEBUG, INFO, WARNING, …).",
    )


def load_app_settings[T: AppSettings](cls: type[T]) -> T:
    """Load a service settings object from environment."""
    return cls()
