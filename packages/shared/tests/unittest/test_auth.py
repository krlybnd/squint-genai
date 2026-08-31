from agentic_shared.crosscut.auth.claims import parse_access_token_claims
from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.service import AuthService
from agentic_shared.crosscut.auth.settings import AuthSettings, RoleSettings


def test_auth_service_api_key_mode() -> None:
    # Arrange
    service = AuthService(
        AuthSettings(auth_mode="api_key", api_key="secret"),
        RoleSettings(),
        jwt_validator=_FakeJwt(),  # type: ignore[arg-type]
    )

    # Act
    denied = service.resolve(authorization=None, x_api_key="wrong")
    allowed = service.resolve(authorization=None, x_api_key="secret")

    # Assert
    assert denied.roles == frozenset()
    assert allowed.has_role(AppRole.ADMIN)


def test_auth_service_maps_keycloak_roles() -> None:
    # Arrange
    service = AuthService(
        AuthSettings(auth_mode="jwt"),
        RoleSettings(),
        jwt_validator=_FakeJwt(),  # type: ignore[arg-type]
    )

    # Act
    ctx = service.resolve(authorization="Bearer test-token")

    # Assert
    assert ctx.user_id == "user-1"
    assert ctx.username == "alice"
    assert ctx.tenant_id == "tenant-a"
    assert ctx.has_role(AppRole.READ)
    assert ctx.has_role(AppRole.WRITE)
    assert not ctx.has_role(AppRole.ADMIN)


def test_auth_service_uses_active_tenant_roles() -> None:
    # Arrange
    service = AuthService(
        AuthSettings(auth_mode="jwt"),
        RoleSettings(),
        jwt_validator=_FakeTenantJwt(),  # type: ignore[arg-type]
    )

    # Act
    ctx = service.resolve(authorization="Bearer test-token")

    # Assert
    assert ctx.tenant_id == "tenant-b"
    assert ctx.roles == frozenset({AppRole.READ})


def test_admin_implies_all_roles() -> None:
    # Arrange
    ctx = AuthContext(user_id="1", tenant_id="tenant-a", roles=frozenset({AppRole.ADMIN}))

    # Assert
    assert ctx.has_role(AppRole.READ)
    assert ctx.has_role(AppRole.WRITE)


def test_parse_access_token_claims_flat_roles() -> None:
    assert parse_access_token_claims({"roles": ["admin", "read"]}).app_roles() == frozenset(
        {AppRole.ADMIN, AppRole.READ}
    )


class _FakeJwt:
    def decode(self, _token: str) -> dict[str, object]:
        return {
            "sub": "user-1",
            "preferred_username": "alice",
            "tenant_id": "tenant-a",
            "roles": ["read", "write"],
        }


class _FakeTenantJwt:
    def decode(self, _token: str) -> dict[str, object]:
        return {
            "sub": "bob",
            "tenant_id": "tenant-b",
            "roles": ["read", "write"],
            "tenant_roles": ['{"tenant-b":["read"],"e2e-1":["read","write"]}'],
        }
