import logging
import secrets

from jwt import PyJWTError

from agentic_shared.crosscut.auth.claims import AccessTokenClaims, parse_access_token_claims
from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.enums import AuthMode
from agentic_shared.crosscut.auth.jwt import JwtValidator
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.settings import AuthSettings, RoleSettings
from agentic_shared.crosscut.auth.tenant import DEFAULT_TENANT_ID

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
            expected = self._auth_settings.api_key.get_secret_value()
            if not x_api_key or not secrets.compare_digest(x_api_key, expected):
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
            raw_claims = self._jwt_validator.decode(token)
        except PyJWTError:
            logger.warning("jwt validation failed")
            return AuthContext(user_id=None, tenant_id=None, roles=frozenset())

        claims = parse_access_token_claims(raw_claims)
        return AuthContext(
            user_id=claims.user_id or None,
            tenant_id=claims.tenant_id or _header_tenant_id(x_tenant_id),
            roles=self._map_roles(claims),
        )

    def _resolve_internal_service(
        self,
        x_internal_service_key: str | None,
        x_tenant_id: str | None,
    ) -> AuthContext | None:
        expected = self._auth_settings.internal_service_key.get_secret_value().strip()
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

    def _map_roles(self, claims: AccessTokenClaims) -> frozenset[AppRole]:
        """Filter claim roles through configured Keycloak→AppRole mapping."""
        mapping = self._role_settings.roles
        return frozenset(
            mapping[role.value] for role in claims.app_roles() if role.value in mapping
        )


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
