"""Admin service settings."""

from agentic_shared.core.auth.settings import AuthSettings, RoleSettings
from agentic_shared.core.settings.app import AppSettings, load_app_settings
from agentic_shared.integrations.keycloak_admin.settings import KeycloakAdminSettings
from pydantic import Field


class AdminSettings(AppSettings):
    auth: AuthSettings = Field(default_factory=AuthSettings)
    role: RoleSettings = Field(default_factory=RoleSettings)
    keycloak_integration: KeycloakAdminSettings = Field(default_factory=KeycloakAdminSettings)


def load_settings() -> AdminSettings:
    return load_app_settings(AdminSettings)


__all__ = ["AdminSettings", "load_settings"]
