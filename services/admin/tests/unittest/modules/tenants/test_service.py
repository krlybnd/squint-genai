import unittest
from unittest.mock import AsyncMock

from agentic_shared.integrations.keycloak_admin.errors import KeycloakNotFoundError
from agentic_shared.integrations.keycloak_admin.gateway import (
    TenantMemberRecord,
    TenantRecord,
    UserRecord,
)

from agentic_admin.modules.tenants.service import TenantAdminService


class TestTenantAdminService(unittest.IsolatedAsyncioTestCase):
    async def test_list_tenants(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        tenant_gateway.list_tenants.return_value = [
            TenantRecord(id="1", alias="acme", name="Acme Corp", enabled=True),
        ]
        service = TenantAdminService(tenant_gateway, AsyncMock())

        # Act
        tenants = await service.list_tenants()

        # Assert
        tenant_gateway.list_tenants.assert_awaited_once()
        self.assertEqual(len(tenants), 1)
        self.assertEqual(tenants[0].alias, "acme")

    async def test_create_tenant(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        tenant_gateway.create_tenant.return_value = TenantRecord(
            id="1", alias="acme", name="Acme Corp", enabled=True
        )
        service = TenantAdminService(tenant_gateway, AsyncMock())

        # Act
        out = await service.create_tenant(alias="acme", name="Acme Corp")

        # Assert
        tenant_gateway.create_tenant.assert_awaited_once_with(alias="acme", name="Acme Corp")
        self.assertEqual(out.alias, "acme")
        self.assertEqual(out.name, "Acme Corp")

    async def test_update_tenant(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        tenant_gateway.update_tenant.return_value = TenantRecord(
            id="1", alias="acme", name="Acme Inc", enabled=False
        )
        service = TenantAdminService(tenant_gateway, AsyncMock())

        # Act
        out = await service.update_tenant("acme", name="Acme Inc", enabled=False)

        # Assert
        tenant_gateway.update_tenant.assert_awaited_once_with(
            "acme", name="Acme Inc", enabled=False
        )
        self.assertEqual(out.name, "Acme Inc")
        self.assertFalse(out.enabled)

    async def test_delete_tenant(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        service = TenantAdminService(tenant_gateway, AsyncMock())

        # Act
        await service.delete_tenant("acme")

        # Assert
        tenant_gateway.delete_tenant.assert_awaited_once_with("acme")

    async def test_list_members(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        tenant_gateway.list_members.return_value = (
            [
                TenantMemberRecord(
                    id="u1", username="alice", email="alice@example.com", roles=["read"]
                )
            ],
            True,
        )
        service = TenantAdminService(tenant_gateway, AsyncMock())

        # Act
        members, has_more = await service.list_members("acme", first=0, max_results=10)

        # Assert
        tenant_gateway.list_members.assert_awaited_once_with("acme", first=0, max_results=10)
        self.assertTrue(has_more)
        self.assertEqual(members[0].username, "alice")
        self.assertEqual(members[0].roles, ["read"])

    async def test_add_member_happy_path(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        tenant_gateway.list_members.return_value = (
            [
                TenantMemberRecord(
                    id="u1", username="alice", email="alice@example.com", roles=["write"]
                )
            ],
            False,
        )
        user_gateway = AsyncMock()
        service = TenantAdminService(tenant_gateway, user_gateway)

        # Act
        member = await service.add_member("acme", "alice", roles=["write"])

        # Assert
        user_gateway.assign_tenant.assert_awaited_once_with("alice", "acme", roles=["write"])
        self.assertEqual(member.username, "alice")
        self.assertEqual(member.email, "alice@example.com")
        self.assertEqual(member.roles, ["write"])

    async def test_add_member_falls_back_to_user_lookup(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        tenant_gateway.list_members.return_value = ([], False)
        user_gateway = AsyncMock()
        user_gateway.get_by_username.return_value = UserRecord(
            id="u1",
            username="alice",
            email="alice@example.com",
            enabled=True,
            tenant_id=None,
            tenant_ids=[],
            realm_roles=[],
            tenant_roles={},
        )
        service = TenantAdminService(tenant_gateway, user_gateway)

        # Act
        member = await service.add_member("acme", "alice")

        # Assert
        self.assertEqual(member.username, "alice")
        user_gateway.assign_tenant.assert_awaited_once_with("alice", "acme", roles=None)

    async def test_update_member_roles(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        user_gateway = AsyncMock()
        user_gateway.set_tenant_roles.return_value = UserRecord(
            id="u1",
            username="alice",
            email="alice@example.com",
            enabled=True,
            tenant_id="acme",
            tenant_ids=["acme"],
            realm_roles=["admin"],
            tenant_roles={"acme": ["admin"]},
        )
        service = TenantAdminService(tenant_gateway, user_gateway)

        # Act
        member = await service.update_member_roles("acme", "alice", ["admin"])

        # Assert
        user_gateway.set_tenant_roles.assert_awaited_once_with("alice", "acme", ["admin"])
        self.assertEqual(member.roles, ["admin"])

    async def test_add_member_not_found(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        tenant_gateway.list_members.return_value = ([], False)
        user_gateway = AsyncMock()
        user_gateway.get_by_username.return_value = None
        service = TenantAdminService(tenant_gateway, user_gateway)

        # Act / Assert
        with self.assertRaises(KeycloakNotFoundError):
            await service.add_member("acme", "missing")

    async def test_remove_member(self) -> None:
        # Arrange
        tenant_gateway = AsyncMock()
        user_gateway = AsyncMock()
        service = TenantAdminService(tenant_gateway, user_gateway)

        # Act
        await service.remove_member("acme", "alice")

        # Assert
        user_gateway.remove_from_tenant_org.assert_awaited_once_with("alice", "acme")


if __name__ == "__main__":
    unittest.main()
