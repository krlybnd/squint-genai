import unittest
from unittest.mock import AsyncMock

from agentic_shared.integrations.idp.core.errors import IdpForbiddenError, IdpNotFoundError
from agentic_shared.integrations.idp.core.records import TenantRecord, UserRecord
from agentic_shared.integrations.idp.keycloak.user.tenancy import KeycloakUserTenancy


def _user(*, tenant_id: str = "tenant-a", tenant_ids: list[str] | None = None) -> UserRecord:
    aliases = tenant_ids if tenant_ids is not None else ["tenant-a", "tenant-b"]
    return UserRecord(
        id="1",
        username="admin",
        email="admin@local",
        enabled=True,
        tenant_id=tenant_id,
        tenant_ids=aliases,
        realm_roles=["admin"],
        tenant_roles={},
    )


class TestKeycloakUserTenancy(unittest.IsolatedAsyncioTestCase):
    async def test_get_lists_membership_tenants_with_names(self) -> None:
        # Arrange
        users = AsyncMock()
        users.get_by_username.return_value = _user()
        tenants = AsyncMock()
        tenants.list_tenants.return_value = [
            TenantRecord(id="a", alias="tenant-a", name="Tenant A", enabled=True),
            TenantRecord(id="b", alias="tenant-b", name="Tenant B", enabled=True),
            TenantRecord(id="c", alias="other", name="Other", enabled=True),
        ]
        adapter = KeycloakUserTenancy(users, tenants)

        # Act
        tenancy = await adapter.get("admin")

        # Assert
        assert tenancy is not None
        self.assertEqual(tenancy.username, "admin")
        self.assertEqual(tenancy.tenant_id, "tenant-a")
        self.assertEqual(
            [(t.alias, t.name) for t in tenancy.tenants],
            [("tenant-a", "Tenant A"), ("tenant-b", "Tenant B")],
        )

    async def test_get_unknown_user(self) -> None:
        # Arrange
        users = AsyncMock()
        users.get_by_username.return_value = None
        adapter = KeycloakUserTenancy(users, AsyncMock())

        # Act
        tenancy = await adapter.get("ghost")

        # Assert
        self.assertIsNone(tenancy)

    async def test_set_active_rejects_non_member(self) -> None:
        # Arrange
        users = AsyncMock()
        users.get_by_username.return_value = _user(tenant_ids=["tenant-a"])
        tenants = AsyncMock()
        tenants.list_tenants.return_value = [
            TenantRecord(id="a", alias="tenant-a", name="Tenant A", enabled=True),
        ]
        adapter = KeycloakUserTenancy(users, tenants)

        # Act / Assert
        with self.assertRaises(IdpForbiddenError):
            await adapter.set_active("admin", "tenant-b")
        users.set_active_tenant.assert_not_awaited()

    async def test_set_active_switches_when_member(self) -> None:
        # Arrange
        users = AsyncMock()
        users.get_by_username.side_effect = [
            _user(tenant_id="tenant-a"),
            _user(tenant_id="tenant-b"),
        ]
        tenants = AsyncMock()
        tenants.list_tenants.return_value = [
            TenantRecord(id="a", alias="tenant-a", name="Tenant A", enabled=True),
            TenantRecord(id="b", alias="tenant-b", name="Tenant B", enabled=True),
        ]
        adapter = KeycloakUserTenancy(users, tenants)

        # Act
        tenancy = await adapter.set_active("admin", "tenant-b")

        # Assert
        users.set_active_tenant.assert_awaited_once_with("admin", "tenant-b")
        self.assertEqual(tenancy.tenant_id, "tenant-b")

    async def test_set_active_unknown_user(self) -> None:
        # Arrange
        users = AsyncMock()
        users.get_by_username.return_value = None
        adapter = KeycloakUserTenancy(users, AsyncMock())

        # Act / Assert
        with self.assertRaises(IdpNotFoundError):
            await adapter.set_active("ghost", "tenant-a")
