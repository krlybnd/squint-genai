"""Admin service settings."""

from agentic_shared.core.compliance.settings import ComplianceSettings
from agentic_shared.core.settings.app import AppSettings, load_app_settings
from agentic_shared.crosscut.auth.settings import AuthSettings, RoleSettings
from agentic_shared.frameworks.fastapi.defaults import FrameworkDefaults
from agentic_shared.frameworks.fastapi.settings import FastAPISettings
from agentic_shared.infrastructure.sql.postgres.settings import DatabaseSettings
from agentic_shared.integrations.idp.keycloak.settings import KeycloakAdminSettings
from pydantic import Field


class AdminSettings(AppSettings):
    """Composed settings for tenant/user admin (Keycloak Organizations)."""

    defaults: FrameworkDefaults = Field(
        default_factory=lambda: FrameworkDefaults.from_distribution("agentic-admin"),
        description="Service identity from pyproject (name / version / description).",
    )
    fastapi: FastAPISettings = Field(
        default_factory=FastAPISettings,
        description="FastAPI CORS, OpenAPI docs paths, security headers.",
    )
    auth: AuthSettings = Field(
        default_factory=AuthSettings,
        description="Inbound request authentication (JWT / API key / none).",
    )
    role: RoleSettings = Field(
        default_factory=RoleSettings,
        description="IdP realm role → AppRole mapping for authorization.",
    )
    keycloak_integration: KeycloakAdminSettings = Field(
        default_factory=KeycloakAdminSettings,
        description="Keycloak Admin API client-credentials integration.",
    )
    compliance: ComplianceSettings = Field(
        default_factory=ComplianceSettings,
        description="Audit log toggle for tenant/user mutations.",
    )
    database: DatabaseSettings = Field(
        default_factory=DatabaseSettings,
        description="PostgreSQL for append-only audit_events when compliance is enabled.",
    )


def load_settings() -> AdminSettings:
    return load_app_settings(AdminSettings)


__all__ = ["AdminSettings", "load_settings"]
