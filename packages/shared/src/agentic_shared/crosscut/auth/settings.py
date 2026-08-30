import json

from pydantic import Field, field_validator

from agentic_shared.core.settings.base import EnvSettings
from agentic_shared.core.settings.secrets import SecuredStr
from agentic_shared.crosscut.auth.enums import AuthMode
from agentic_shared.crosscut.auth.roles import AppRole

DEFAULT_ROLE_MAPPING: dict[str, AppRole] = {
    "admin": AppRole.ADMIN,
    "read": AppRole.READ,
    "write": AppRole.WRITE,
}


class RoleSettings(EnvSettings):
    """Maps Keycloak realm role names to application roles."""

    title: str = Field(
        default="auth",
        description="Log label for role-mapping settings (paired with AuthSettings).",
    )
    roles: dict[str, AppRole] = Field(
        default_factory=lambda: dict(DEFAULT_ROLE_MAPPING),
        description=(
            "Map of IdP realm role name → AppRole. "
            "Env may be JSON or loose `{admin:admin,...}` form."
        ),
    )

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
    """Request authentication mode and Keycloak / API-key credentials."""

    title: str = Field(default="auth", description="Log label for auth settings.")
    auth_mode: AuthMode = Field(
        default=AuthMode.JWT,
        description="How inbound requests are authenticated: jwt | api_key | none.",
    )
    keycloak_url: str = Field(
        default="http://localhost:8080",
        description="Keycloak base URL used to fetch JWKS / validate JWTs.",
    )
    keycloak_realm: str = Field(
        default="agentic-rag-eval",
        description="Realm whose tokens are accepted by JWT auth.",
    )
    api_key: SecuredStr = Field(
        default=SecuredStr("dev-admin-key-change-me"),
        description="Shared secret when auth_mode=api_key (dev/ops callers).",
    )
    internal_service_key: SecuredStr = Field(
        default=SecuredStr(""),
        description="Optional key for service-to-service calls; empty disables the path.",
    )
