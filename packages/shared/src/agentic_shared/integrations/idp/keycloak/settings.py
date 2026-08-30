from pydantic import Field

from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.integrations.core.settings import IntegrationSettings


class KeycloakAdminSettings(IntegrationSettings):
    """Keycloak Admin API (client-credentials) for tenant/user administration."""

    title: str = Field(
        default="keycloak-admin",
        description="Readiness/log label for the Keycloak admin integration.",
    )
    keycloak_url: str = Field(
        default="http://localhost:8080",
        description="Keycloak server base URL (no trailing realm path).",
    )
    keycloak_realm: str = Field(
        default="agentic-rag-eval",
        description="Realm that owns Organizations / users managed by admin APIs.",
    )
    keycloak_admin_client_id: str = Field(
        default="agentic-rag-eval-api",
        description="Confidential client id used for client-credentials token requests.",
    )
    keycloak_admin_client_secret: SecuredStr = Field(
        default=SecuredStr("change-me-api-client-secret"),
        description="Confidential client secret for the admin API client.",
    )
