import json

from pydantic import Field, field_validator

from agentic_shared.core.auth.enums import AuthMode
from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.settings.base import EnvSettings

DEFAULT_ROLE_MAPPING: dict[str, AppRole] = {
    "admin": AppRole.ADMIN,
    "read": AppRole.READ,
    "write": AppRole.WRITE,
}


class RoleSettings(EnvSettings):
    """Maps Keycloak realm role names to application roles."""

    title: str = "auth"
    roles: dict[str, AppRole] = Field(default_factory=lambda: dict(DEFAULT_ROLE_MAPPING))

    @field_validator("roles", mode="before")
    @classmethod
    def parse_roles(cls, value: object) -> object:
        if isinstance(value, str):
            parsed = json.loads(value)
            return {key: AppRole(role) for key, role in parsed.items()}
        return value


class AuthSettings(EnvSettings):
    title: str = "auth"
    auth_mode: AuthMode = AuthMode.JWT
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "agentic-rag-eval"
    api_key: str = "dev-admin-key-change-me"
    internal_service_key: str = ""
