import unittest
from unittest.mock import AsyncMock

from agentic_shared.integrations.keycloak_admin.errors import KeycloakNotFoundError
from agentic_shared.integrations.keycloak_admin.gateway import UserRecord

from agentic_admin.modules.users.schemas import UpdateUserRequest
from agentic_admin.modules.users.service import UserAdminService


class TestUserAdminService(unittest.IsolatedAsyncioTestCase):
    async def test_list_users_skips_service_accounts(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.list_users.return_value = (
            [
                UserRecord(
                    id="1",
                    username="service-account-bot",
                    email=None,
                    enabled=True,
                    tenant_id=None,
                    tenant_ids=[],
                    realm_roles=[],
                ),
                UserRecord(
                    id="2",
                    username="alice",
                    email="alice@example.com",
                    enabled=True,
                    tenant_id="acme",
                    tenant_ids=["acme"],
                    realm_roles=["write"],
                ),
            ],
            False,
        )
        service = UserAdminService(gateway)

        # Act
        users, has_more = await service.list_users()

        # Assert
        self.assertFalse(has_more)
        self.assertEqual([u.username for u in users], ["alice"])

    async def test_get_user_not_found(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.get_by_username.return_value = None
        service = UserAdminService(gateway)

        # Act / Assert
        with self.assertRaises(KeycloakNotFoundError):
            await service.get_user("missing")

    async def test_list_users_pagination_passthrough(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.list_users.return_value = (
            [
                UserRecord(
                    id="2",
                    username="alice",
                    email="alice@example.com",
                    enabled=True,
                    tenant_id="acme",
                    tenant_ids=["acme"],
                    realm_roles=["write"],
                ),
            ],
            True,
        )
        service = UserAdminService(gateway)

        # Act
        users, has_more = await service.list_users(search="ali", first=10, max_results=5)

        # Assert
        gateway.list_users.assert_awaited_once_with(search="ali", first=10, max_results=5)
        self.assertTrue(has_more)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].username, "alice")

    async def test_create_user(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.create_user.return_value = UserRecord(
            id="1",
            username="bob",
            email="bob@example.com",
            enabled=True,
            tenant_id=None,
            tenant_ids=[],
            realm_roles=["read"],
        )
        service = UserAdminService(gateway)

        # Act
        out = await service.create_user(
            username="bob",
            email="bob@example.com",
            password="secret",
            realm_roles=["read"],
        )

        # Assert
        gateway.create_user.assert_awaited_once_with(
            username="bob",
            email="bob@example.com",
            password="secret",
            realm_roles=["read"],
        )
        self.assertEqual(out.username, "bob")
        self.assertEqual(out.realm_roles, ["read"])

    async def test_assign_tenant(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.assign_tenant.return_value = UserRecord(
            id="1",
            username="alice",
            email="alice@example.com",
            enabled=True,
            tenant_id="acme",
            tenant_ids=["acme"],
            realm_roles=["write"],
        )
        service = UserAdminService(gateway)

        # Act
        out = await service.assign_tenant("alice", "acme", set_active=True)

        # Assert
        gateway.assign_tenant.assert_awaited_once_with("alice", "acme", set_active=True)
        self.assertEqual(out.tenant_id, "acme")

    async def test_set_active_tenant(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.set_active_tenant.return_value = UserRecord(
            id="1",
            username="alice",
            email="alice@example.com",
            enabled=True,
            tenant_id="beta",
            tenant_ids=["acme", "beta"],
            realm_roles=["write"],
        )
        service = UserAdminService(gateway)

        # Act
        out = await service.set_active_tenant("alice", "beta")

        # Assert
        gateway.set_active_tenant.assert_awaited_once_with("alice", "beta")
        self.assertEqual(out.tenant_id, "beta")

    async def test_remove_tenant(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.remove_tenant.return_value = UserRecord(
            id="1",
            username="alice",
            email="alice@example.com",
            enabled=True,
            tenant_id=None,
            tenant_ids=["acme"],
            realm_roles=["write"],
        )
        service = UserAdminService(gateway)

        # Act
        out = await service.remove_tenant("alice")

        # Assert
        gateway.remove_tenant.assert_awaited_once_with("alice")
        self.assertIsNone(out.tenant_id)

    async def test_remove_from_tenant(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.remove_from_tenant_org.return_value = UserRecord(
            id="1",
            username="alice",
            email="alice@example.com",
            enabled=True,
            tenant_id="acme",
            tenant_ids=["acme"],
            realm_roles=["write"],
        )
        service = UserAdminService(gateway)

        # Act
        out = await service.remove_from_tenant("alice", "beta")

        # Assert
        gateway.remove_from_tenant_org.assert_awaited_once_with("alice", "beta")
        self.assertEqual(out.username, "alice")

    async def test_update_user_assigns_tenant_without_clear(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.update_user.return_value = UserRecord(
            id="1",
            username="alice",
            email="alice@example.com",
            enabled=True,
            tenant_id="acme",
            tenant_ids=["acme"],
            realm_roles=["write"],
        )
        service = UserAdminService(gateway)

        # Act
        out = await service.update_user(
            "alice",
            UpdateUserRequest(email="alice@example.com", tenant_id="acme"),
        )

        # Assert
        gateway.update_user.assert_awaited_once()
        call_kwargs = gateway.update_user.await_args.kwargs
        self.assertEqual(call_kwargs["tenant_alias"], "acme")
        self.assertFalse(call_kwargs["clear_tenant"])
        self.assertEqual(out.tenant_id, "acme")

    async def test_update_user_clear_tenant(self) -> None:
        # Arrange
        gateway = AsyncMock()
        gateway.update_user.return_value = UserRecord(
            id="1",
            username="alice",
            email="alice@example.com",
            enabled=True,
            tenant_id=None,
            tenant_ids=[],
            realm_roles=["write"],
        )
        service = UserAdminService(gateway)

        # Act
        out = await service.update_user("alice", UpdateUserRequest(tenant_id=""))

        # Assert
        gateway.update_user.assert_awaited_once()
        self.assertIsNone(out.tenant_id)
        call_kwargs = gateway.update_user.await_args.kwargs
        self.assertTrue(call_kwargs["clear_tenant"])


if __name__ == "__main__":
    unittest.main()
