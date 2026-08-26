import unittest

from starlette.exceptions import HTTPException

from agentic_shared.core.auth.context import AuthContext
from agentic_shared.core.auth.enums import AuthMode
from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.settings import AuthSettings
from agentic_shared.frameworks.fastapi.auth.dependencies import require_roles


class TestRequireRoles(unittest.TestCase):
    def test_none_mode_skips_all_checks(self) -> None:
        # Arrange
        auth = AuthContext(user_id=None, tenant_id=None, roles=frozenset())
        settings = AuthSettings(auth_mode=AuthMode.NONE)

        # Act / Assert
        require_roles(auth, settings, AppRole.ADMIN)

    def test_jwt_without_user_raises_401(self) -> None:
        # Arrange
        auth = AuthContext(user_id=None, tenant_id="tenant-1", roles=frozenset())
        settings = AuthSettings(auth_mode=AuthMode.JWT)

        # Act / Assert
        with self.assertRaises(HTTPException) as ctx:
            require_roles(auth, settings, AppRole.READ)
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "Unauthorized")

    def test_authenticated_without_role_raises_403(self) -> None:
        # Arrange
        auth = AuthContext(user_id="user-1", tenant_id="tenant-1", roles=frozenset({AppRole.READ}))
        settings = AuthSettings(auth_mode=AuthMode.JWT)

        # Act / Assert
        with self.assertRaises(HTTPException) as ctx:
            require_roles(auth, settings, AppRole.WRITE)
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "Forbidden")

    def test_api_key_without_role_raises_403_not_401(self) -> None:
        # Arrange
        auth = AuthContext(user_id="api-key-user", tenant_id="tenant-1", roles=frozenset())
        settings = AuthSettings(auth_mode=AuthMode.API_KEY, api_key="secret")

        # Act / Assert
        with self.assertRaises(HTTPException) as ctx:
            require_roles(auth, settings, AppRole.READ)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_matching_role_passes(self) -> None:
        # Arrange
        auth = AuthContext(user_id="user-1", tenant_id="tenant-1", roles=frozenset({AppRole.WRITE}))
        settings = AuthSettings(auth_mode=AuthMode.JWT)

        # Act / Assert
        require_roles(auth, settings, AppRole.WRITE)


if __name__ == "__main__":
    unittest.main()
