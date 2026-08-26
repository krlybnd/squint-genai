from dishka import Provider, Scope, provide
from starlette.requests import Request

from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.jwt import JwtValidator
from agentic_shared.core.auth.service import AuthService
from agentic_shared.core.auth.settings import AuthSettings, RoleSettings


class AuthProvider(Provider):
    def __init__(self, auth: AuthSettings, role: RoleSettings) -> None:
        super().__init__()
        self._auth = auth
        self._role = role

    @provide(scope=Scope.APP)
    def auth_settings(self) -> AuthSettings:
        return self._auth

    @provide(scope=Scope.APP)
    def role_settings(self) -> RoleSettings:
        return self._role

    @provide(scope=Scope.APP)
    def jwt_validator(self) -> JwtValidator:
        return JwtValidator(self._auth)

    @provide(scope=Scope.APP)
    def auth_service(self, jwt_validator: JwtValidator) -> AuthService:
        return AuthService(self._auth, self._role, jwt_validator)

    @provide(scope=Scope.REQUEST)
    def auth_context(self, request: Request, auth_service: AuthService) -> AuthContext:
        return auth_service.resolve(
            authorization=request.headers.get("Authorization"),
            x_api_key=request.headers.get("X-API-Key"),
            x_tenant_id=request.headers.get("X-Tenant-Id"),
            x_internal_service_key=request.headers.get("X-Internal-Service-Key"),
        )
