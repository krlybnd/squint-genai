import unittest
from unittest.mock import AsyncMock

from agentic_shared.integrations.idp.core.errors import IdpForbiddenError, IdpNotFoundError
from agentic_shared.integrations.idp.core.records import TenantRecord, UserTenancy

from agentic_api.modules.me.service import MeService


def _tenancy(*, tenant_id: str = "tenant-a") -> UserTenancy:
    return UserTenancy(
        username="admin",
        tenant_id=tenant_id,
        tenants=[
            TenantRecord(id="a", alias="tenant-a", name="Tenant A", enabled=True),
            TenantRecord(id="b", alias="tenant-b", name="Tenant B", enabled=True),
        ],
    )


class TestMeService(unittest.IsolatedAsyncioTestCase):
    async def test_get_me_maps_tenancy(self) -> None:
        # Arrange
        reader = AsyncMock()
        reader.get.return_value = _tenancy()
        service = MeService(reader, AsyncMock())

        # Act
        me = await service.get_me("admin")

        # Assert
        reader.get.assert_awaited_once_with("admin")
        self.assertEqual(me.username, "admin")
        self.assertEqual(me.tenant_id, "tenant-a")
        self.assertEqual(
            [(t.alias, t.name) for t in me.tenants],
            [("tenant-a", "Tenant A"), ("tenant-b", "Tenant B")],
        )

    async def test_get_me_unknown_user(self) -> None:
        # Arrange
        reader = AsyncMock()
        reader.get.return_value = None
        service = MeService(reader, AsyncMock())

        # Act / Assert
        with self.assertRaises(IdpNotFoundError):
            await service.get_me("ghost")

    async def test_set_active_tenant_maps_writer(self) -> None:
        # Arrange
        writer = AsyncMock()
        writer.set_active.return_value = _tenancy(tenant_id="tenant-b")
        service = MeService(AsyncMock(), writer)

        # Act
        me = await service.set_active_tenant("admin", "tenant-b")

        # Assert
        writer.set_active.assert_awaited_once_with("admin", "tenant-b")
        self.assertEqual(me.tenant_id, "tenant-b")

    async def test_set_active_tenant_propagates_forbidden(self) -> None:
        # Arrange
        writer = AsyncMock()
        writer.set_active.side_effect = IdpForbiddenError("Not a member of tenant: tenant-b")
        service = MeService(AsyncMock(), writer)

        # Act / Assert
        with self.assertRaises(IdpForbiddenError):
            await service.set_active_tenant("admin", "tenant-b")
