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

    @staticmethod
    def _parse_loose_role_map(value: str) -> dict[str, str]:
        """Parse bash-sourced ``ROLES={admin:admin,...}`` after JSON quotes are stripped."""
        trimmed = value.strip()
        if trimmed.startswith("{") and trimmed.endswith("}"):
            trimmed = trimmed[1:-1]
        parsed: dict[str, str] = {}
        for part in trimmed.split(","):
            if ":" not in part:
                continue
            key, role = part.split(":", 1)
            parsed[key.strip()] = role.strip()
        return parsed

    @field_validator("roles", mode="before")
    @classmethod
    def parse_roles(cls, value: object) -> object:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = cls._parse_loose_role_map(value)
            return {key: AppRole(role) for key, role in parsed.items()}
        return value


class AuthSettings(EnvSettings):
    title: str = "auth"
    auth_mode: AuthMode = AuthMode.JWT
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "agentic-rag-eval"
    api_key: str = "dev-admin-key-change-me"
    internal_service_key: str = ""
