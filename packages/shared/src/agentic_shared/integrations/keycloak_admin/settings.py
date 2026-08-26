from agentic_shared.core.settings.base import EnvSettings


class KeycloakAdminSettings(EnvSettings):
    title: str = "keycloak-admin"
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "agentic-rag-eval"
    keycloak_admin_client_id: str = "agentic-rag-eval-api"
    keycloak_admin_client_secret: str = "change-me-api-client-secret"
