import unittest
from unittest.mock import AsyncMock, MagicMock

from agentic_shared.integrations.idp.core.errors import IdpForbiddenError
from agentic_shared.integrations.idp.core.records import UserRecord, UserTenancy
from agentic_shared.integrations.idp.keycloak.user.tenancy import KeycloakUserTenancy


def _user(**overrides: object) -> UserRecord:
    defaults: dict[str, object] = {
        "id": "u1",
        "username": "alice",
        "email": "alice@example.com",
        "enabled": True,
        "tenant_id": "tenant-a",
        "tenant_ids": ["tenant-a", "tenant-b"],
        "realm_roles": ["read"],
        "tenant_roles": {"tenant-a": ["read", "write"], "tenant-b": ["read"]},
    }
    defaults.update(overrides)
    return UserRecord(**defaults)  # type: ignore[arg-type]


class TestKeycloakUserTenancy(unittest.IsolatedAsyncioTestCase):
    async def test_get_uses_user_memberships_not_org_catalog(self) -> None:
        # Arrange
        users = MagicMock()
        users.get_by_username = AsyncMock(return_value=_user())
        tenancy = KeycloakUserTenancy(users)

        # Act
        got = await tenancy.get("alice")

        # Assert
        self.assertIsInstance(got, UserTenancy)
        assert got is not None
        self.assertEqual([t.alias for t in got.tenants], ["tenant-a", "tenant-b"])
        self.assertEqual(got.tenants[0].name, "tenant-a")
        users.get_by_username.assert_awaited_once_with("alice")

    async def test_set_active_rejects_unknown_membership(self) -> None:
        # Arrange
        users = MagicMock()
        users.get_by_username = AsyncMock(return_value=_user())
        users.set_active_tenant = AsyncMock()
        tenancy = KeycloakUserTenancy(users)

        # Act / Assert
        with self.assertRaises(IdpForbiddenError):
            await tenancy.set_active("alice", "tenant-z")
        users.set_active_tenant.assert_not_awaited()

    async def test_set_active_writes_user_attribute(self) -> None:
        # Arrange
        users = MagicMock()
        users.get_by_username = AsyncMock(
            side_effect=[
                _user(),
                _user(tenant_id="tenant-b"),
            ]
        )
        users.set_active_tenant = AsyncMock()
        tenancy = KeycloakUserTenancy(users)

        # Act
        got = await tenancy.set_active("alice", "tenant-b")

        # Assert
        users.set_active_tenant.assert_awaited_once_with("alice", "tenant-b")
        self.assertEqual(got.tenant_id, "tenant-b")


if __name__ == "__main__":
    unittest.main()
