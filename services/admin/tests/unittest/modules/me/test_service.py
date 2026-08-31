import unittest
from unittest.mock import AsyncMock

from agentic_shared.integrations.idp.core.errors import IdpForbiddenError, IdpNotFoundError
from agentic_shared.integrations.idp.core.records import TenantRecord, UserRecord

from agentic_admin.modules.me.service import MeService


class TestMeService(unittest.IsolatedAsyncioTestCase):
    def _user(
        self, *, tenant_id: str = "tenant-a", tenant_ids: list[str] | None = None
    ) -> UserRecord:
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

    async def test_get_me_lists_membership_tenants_with_names(self) -> None:
        # Arrange
        users = AsyncMock()
        users.get_by_username.return_value = self._user()
        tenants = AsyncMock()
        tenants.list_tenants.return_value = [
            TenantRecord(id="a", alias="tenant-a", name="Tenant A", enabled=True),
            TenantRecord(id="b", alias="tenant-b", name="Tenant B", enabled=True),
            TenantRecord(id="c", alias="other", name="Other", enabled=True),
        ]
        service = MeService(users, tenants)

        # Act
        me = await service.get_me("admin")

        # Assert
        self.assertEqual(me.username, "admin")
        self.assertEqual(me.tenant_id, "tenant-a")
        self.assertEqual(
            [(t.alias, t.name) for t in me.tenants],
            [("tenant-a", "Tenant A"), ("tenant-b", "Tenant B")],
        )

    async def test_get_me_unknown_user(self) -> None:
        # Arrange
        users = AsyncMock()
        users.get_by_username.return_value = None
        service = MeService(users, AsyncMock())

        # Act / Assert
        with self.assertRaises(IdpNotFoundError):
            await service.get_me("ghost")

    async def test_set_active_tenant_rejects_non_member(self) -> None:
        # Arrange
        users = AsyncMock()
        users.get_by_username.return_value = self._user(tenant_ids=["tenant-a"])
        service = MeService(users, AsyncMock())

        # Act / Assert
        with self.assertRaises(IdpForbiddenError):
            await service.set_active_tenant("admin", "tenant-b")
        users.set_active_tenant.assert_not_awaited()

    async def test_set_active_tenant_switches_when_member(self) -> None:
        # Arrange
        users = AsyncMock()
        users.get_by_username.side_effect = [
            self._user(tenant_id="tenant-a"),
            self._user(tenant_id="tenant-b"),
        ]
        users.set_active_tenant.return_value = self._user(tenant_id="tenant-b")
        tenants = AsyncMock()
        tenants.list_tenants.return_value = [
            TenantRecord(id="a", alias="tenant-a", name="Tenant A", enabled=True),
            TenantRecord(id="b", alias="tenant-b", name="Tenant B", enabled=True),
        ]
        service = MeService(users, tenants)

        # Act
        me = await service.set_active_tenant("admin", "tenant-b")

        # Assert
        users.set_active_tenant.assert_awaited_once_with("admin", "tenant-b")
        self.assertEqual(me.tenant_id, "tenant-b")
