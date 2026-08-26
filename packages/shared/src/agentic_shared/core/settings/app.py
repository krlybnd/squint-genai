from agentic_shared.core.settings.base import EnvSettings


class AppSettings(EnvSettings):
    """Base for service-level composed settings (api, chat, admin, indexing)."""

    log_level: str = "INFO"


def load_app_settings[T: AppSettings](cls: type[T]) -> T:
    """Load a service settings object from environment."""
    return cls()
