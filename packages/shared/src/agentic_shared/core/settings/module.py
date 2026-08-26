from collections.abc import Callable
from functools import lru_cache

from agentic_shared.core.settings.base import EnvSettings


class ModuleSettings(EnvSettings):
    """Base for vertical-slice module tunables (prompts, limits, env_prefix)."""


def module_settings_loader[T: ModuleSettings](cls: type[T]) -> Callable[[], T]:
    """Return a cached loader for a module settings class."""

    @lru_cache
    def get_module_settings() -> T:
        return cls()

    return get_module_settings
