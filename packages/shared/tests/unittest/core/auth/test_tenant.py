import unittest

from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.service import AuthService
from agentic_shared.core.auth.settings import AuthSettings, RoleSettings
from agentic_shared.core.auth.tenant import resolve_tenant_id


class _StubJwt:
    def decode(self, _token: str) -> dict:
        return {"sub": "user-1", "tenant_id": "tenant-a", "realm_access": {"roles": ["write"]}}


class TestAuthTenant(unittest.TestCase):
    def test_internal_service_key_sets_tenant(self) -> None:
        # Arrange
        auth = AuthSettings(auth_mode="jwt", internal_service_key="secret-key")
        service = AuthService(auth, RoleSettings(), _StubJwt())  # type: ignore[arg-type]

        # Act
        ctx = service.resolve(
            authorization=None,
            x_internal_service_key="secret-key",
            x_tenant_id="tenant-b",
        )

        # Assert
        self.assertEqual(ctx.user_id, "internal-service")
        self.assertEqual(ctx.tenant_id, "tenant-b")
        self.assertTrue(ctx.has_any(AppRole.WRITE))

    def test_jwt_claim_tenant_preferred_over_header(self) -> None:
        # Arrange
        auth = AuthSettings(auth_mode="jwt")
        service = AuthService(auth, RoleSettings(), _StubJwt())  # type: ignore[arg-type]

        # Act
        ctx = service.resolve(authorization="Bearer fake", x_tenant_id="tenant-other")

        # Assert
        self.assertEqual(ctx.tenant_id, "tenant-a")

    def test_api_key_uses_x_tenant_id(self) -> None:
        # Arrange
        auth = AuthSettings(auth_mode="api_key", api_key="k")
        service = AuthService(auth, RoleSettings(), _StubJwt())  # type: ignore[arg-type]

        # Act
        ctx = service.resolve(x_api_key="k", x_tenant_id="tenant-x")

        # Assert
        self.assertEqual(resolve_tenant_id(ctx), "tenant-x")

    def test_anonymous_none_mode(self) -> None:
        # Arrange
        auth = AuthSettings(auth_mode="none")
        service = AuthService(auth, RoleSettings(), _StubJwt())  # type: ignore[arg-type]

        # Act
        ctx = service.resolve()

        # Assert
        self.assertTrue(ctx.has_any(AppRole.ADMIN))

    def test_empty_jwt_is_unauthenticated(self) -> None:
        # Arrange
        auth = AuthSettings(auth_mode="jwt")
        service = AuthService(auth, RoleSettings(), _StubJwt())  # type: ignore[arg-type]

        # Act
        ctx = service.resolve(authorization=None)

        # Assert
        self.assertIsNone(ctx.user_id)
        self.assertEqual(ctx.roles, frozenset())

    def test_resolve_tenant_id_defaults_when_missing(self) -> None:
        # Arrange
        ctx = AuthContext(user_id=None, tenant_id=None, roles=frozenset())

        # Act / Assert
        self.assertEqual(resolve_tenant_id(ctx), "default")

    def test_invalid_api_key_is_unauthenticated(self) -> None:
        # Arrange
        auth = AuthSettings(auth_mode="api_key", api_key="expected-key")
        service = AuthService(auth, RoleSettings(), _StubJwt())  # type: ignore[arg-type]

        # Act
        ctx = service.resolve(x_api_key="wrong-key", x_tenant_id="tenant-x")

        # Assert
        self.assertIsNone(ctx.user_id)
        self.assertEqual(ctx.roles, frozenset())


if __name__ == "__main__":
    unittest.main()
