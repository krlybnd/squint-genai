import logging
import secrets
from typing import Any

from jwt import PyJWTError

from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.enums import AuthMode
from agentic_shared.core.auth.jwt import JwtValidator
from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.settings import AuthSettings, RoleSettings
from agentic_shared.core.auth.tenant import DEFAULT_TENANT_ID

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(
        self,
        auth_settings: AuthSettings,
        role_settings: RoleSettings,
        jwt_validator: JwtValidator,
    ) -> None:
        self._auth_settings = auth_settings
        self._role_settings = role_settings
        self._jwt_validator = jwt_validator

    def resolve(
        self,
        *,
        authorization: str | None = None,
        x_api_key: str | None = None,
        x_tenant_id: str | None = None,
        x_internal_service_key: str | None = None,
    ) -> AuthContext:
        mode = self._auth_settings.auth_mode
        if mode == AuthMode.NONE:
            return AuthContext.anonymous()

        internal = self._resolve_internal_service(x_internal_service_key, x_tenant_id)
        if internal is not None:
            return internal

        if mode == AuthMode.API_KEY:
            if not x_api_key or not secrets.compare_digest(x_api_key, self._auth_settings.api_key):
                logger.warning("invalid api key")
                return AuthContext(user_id=None, tenant_id=None, roles=frozenset())
            tenant = _header_tenant_id(x_tenant_id) or DEFAULT_TENANT_ID
            return AuthContext(
                user_id="api-key",
                tenant_id=tenant,
                roles=frozenset({AppRole.ADMIN, AppRole.READ, AppRole.WRITE}),
            )

        token = _extract_bearer(authorization)
        if not token:
            return AuthContext(user_id=None, tenant_id=None, roles=frozenset())

        try:
            claims = self._jwt_validator.decode(token)
        except PyJWTError:
            logger.warning("jwt validation failed")
            return AuthContext(user_id=None, tenant_id=None, roles=frozenset())
        jwt_tenant = _claim_tenant_id(claims) or _header_tenant_id(x_tenant_id)
        return AuthContext(
            user_id=_claim_user_id(claims),
            tenant_id=jwt_tenant,
            roles=self._map_roles(claims),
        )

    def _resolve_internal_service(
        self,
        x_internal_service_key: str | None,
        x_tenant_id: str | None,
    ) -> AuthContext | None:
        expected = self._auth_settings.internal_service_key.strip()
        if not expected or not x_internal_service_key:
            return None
        if not secrets.compare_digest(x_internal_service_key, expected):
            return None
        tenant = _header_tenant_id(x_tenant_id) or DEFAULT_TENANT_ID
        return AuthContext(
            user_id="internal-service",
            tenant_id=tenant,
            roles=frozenset({AppRole.READ, AppRole.WRITE}),
        )

    def _map_roles(self, claims: dict[str, Any]) -> frozenset[AppRole]:
        keycloak_roles = _extract_keycloak_roles(claims)
        mapped: set[AppRole] = set()
        for keycloak_role in keycloak_roles:
            app_role = self._role_settings.roles.get(keycloak_role)
            if app_role is not None:
                mapped.add(app_role)
        return frozenset(mapped)


def _header_tenant_id(value: str | None) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def _claim_user_id(claims: dict[str, Any]) -> str:
    for key in ("sub", "preferred_username", "sid", "email"):
        value = claims.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _claim_tenant_id(claims: dict[str, Any]) -> str | None:
    tenant_id = claims.get("tenant_id")
    if isinstance(tenant_id, str) and tenant_id:
        return tenant_id
    if isinstance(tenant_id, list) and tenant_id:
        return str(tenant_id[0])
    return None


def _extract_keycloak_roles(claims: dict[str, Any]) -> set[str]:
    roles: set[str] = set()
    top_level = claims.get("roles")
    if isinstance(top_level, list):
        roles.update(str(role) for role in top_level)
    realm_access = claims.get("realm_access")
    if isinstance(realm_access, dict):
        realm_roles = realm_access.get("roles")
        if isinstance(realm_roles, list):
            roles.update(str(role) for role in realm_roles)
    return roles
