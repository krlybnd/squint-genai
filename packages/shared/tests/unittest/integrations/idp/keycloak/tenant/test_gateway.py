from __future__ import annotations

import sys
import unittest
from http import HTTPStatus
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from support import ClientCtx, http_response, org  # noqa: E402


class TestTenantGateway(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        from agentic_shared.integrations.idp.keycloak import TenantGateway
        from agentic_shared.integrations.idp.keycloak.settings import KeycloakAdminSettings

        self.factory = MagicMock()
        self.factory.authenticated_client = AsyncMock(return_value=ClientCtx())
        self.gateway = TenantGateway(KeycloakAdminSettings(), self.factory)

    async def test_list_tenants_skips_incomplete_and_maps_records(self) -> None:
        from keycloak_admin_client.types import UNSET

        import agentic_shared.integrations.idp.keycloak as kc

        incomplete = org()
        incomplete.id = UNSET

        with patch.object(
            kc.get_admin_realms_realm_organizations,
            "asyncio_detailed",
            new=AsyncMock(return_value=http_response(parsed=[incomplete, org()])),
        ):
            records = await self.gateway.list_tenants()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].alias, "acme")

    async def test_list_tenants_empty_when_parsed_is_not_a_list(self) -> None:
        import agentic_shared.integrations.idp.keycloak as kc

        with patch.object(
            kc.get_admin_realms_realm_organizations,
            "asyncio_detailed",
            new=AsyncMock(return_value=http_response(parsed={"oops": True})),
        ):
            self.assertEqual(await self.gateway.list_tenants(), [])

    async def test_get_by_alias_returns_none_when_missing(self) -> None:
        self.gateway.list_tenants = AsyncMock(return_value=[])  # type: ignore[method-assign]
        self.assertIsNone(await self.gateway.get_by_alias("missing"))

    async def test_create_tenant_conflict_when_alias_exists(self) -> None:
        from agentic_shared.integrations.idp.keycloak import TenantRecord
        from agentic_shared.integrations.idp.keycloak.errors import KeycloakConflictError

        self.gateway.get_by_alias = AsyncMock(  # type: ignore[method-assign]
            return_value=TenantRecord(id="1", alias="acme", name="Acme", enabled=True),
        )

        with self.assertRaises(KeycloakConflictError):
            await self.gateway.create_tenant(alias="acme", name="Acme")

    async def test_create_tenant_uses_location_header(self) -> None:
        import agentic_shared.integrations.idp.keycloak as kc

        self.gateway.get_by_alias = AsyncMock(return_value=None)  # type: ignore[method-assign]

        with patch.object(
            kc.post_admin_realms_realm_organizations,
            "asyncio_detailed",
            new=AsyncMock(
                return_value=http_response(
                    status=HTTPStatus.CREATED,
                    headers={"Location": "https://kc/organizations/new-id"},
                ),
            ),
        ):
            created = await self.gateway.create_tenant(alias="acme", name="Acme")

        self.assertEqual(created.id, "new-id")
        self.assertEqual(created.alias, "acme")

    async def test_delete_tenant_raises_when_missing(self) -> None:
        from agentic_shared.integrations.idp.keycloak.errors import KeycloakNotFoundError

        self.gateway.get_by_alias = AsyncMock(return_value=None)  # type: ignore[method-assign]

        with self.assertRaises(KeycloakNotFoundError):
            await self.gateway.delete_tenant("missing")

    async def test_delete_tenant_calls_keycloak(self) -> None:
        import agentic_shared.integrations.idp.keycloak as kc
        from agentic_shared.integrations.idp.keycloak import TenantRecord

        self.gateway.get_by_alias = AsyncMock(  # type: ignore[method-assign]
            return_value=TenantRecord(id="org-1", alias="acme", name="Acme", enabled=True),
        )

        with patch.object(
            kc.delete_admin_realms_realm_organizations_org_id,
            "asyncio_detailed",
            new=AsyncMock(return_value=http_response(status=HTTPStatus.NO_CONTENT)),
        ) as delete:
            await self.gateway.delete_tenant("acme")

        delete.assert_awaited_once()

    async def test_list_members_reads_roles_from_user_attributes(self) -> None:
        import agentic_shared.integrations.idp.keycloak as kc
        from agentic_shared.integrations.idp.keycloak import TenantRecord

        member_type = type("MemberRepresentation", (), {})
        member = member_type()
        member.id = "u1"
        member.username = "bob@tenant-b.local"
        member.email = "bob@tenant-b.local"

        self.gateway.get_by_alias = AsyncMock(  # type: ignore[method-assign]
            return_value=TenantRecord(id="org-1", alias="acme", name="Acme", enabled=True),
        )
        self.gateway._fetch_user_tenant_roles = AsyncMock(  # type: ignore[method-assign]
            return_value={"acme": ["read", "write"]},
        )

        with (
            patch.object(kc, "MemberRepresentation", member_type),
            patch.object(
                kc.get_admin_realms_realm_organizations_org_id_members,
                "asyncio_detailed",
                new=AsyncMock(return_value=http_response(parsed=[member])),
            ),
        ):
            members, has_more = await self.gateway.list_members("acme")

        self.assertFalse(has_more)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].username, "bob@tenant-b.local")
        self.assertEqual(members[0].roles, ["read", "write"])
        self.gateway._fetch_user_tenant_roles.assert_awaited_once_with("u1")

    async def test_list_tenant_aliases_for_user_uses_member_orgs_not_catalog(self) -> None:
        import agentic_shared.integrations.idp.keycloak as kc

        self.gateway.list_tenants = AsyncMock(  # type: ignore[method-assign]
            side_effect=AssertionError("must not GET /organizations"),
        )

        with patch.object(
            kc.get_admin_realms_realm_organizations_members_member_id_organizations,
            "asyncio_detailed",
            new=AsyncMock(
                return_value=http_response(
                    parsed=[
                        org(alias="tenant-b", name="Tenant B"),
                        org(org_id="org-2", alias="tenant-a", name="Tenant A"),
                    ]
                )
            ),
        ):
            aliases = await self.gateway.list_tenant_aliases_for_user("u1")

        self.assertEqual(aliases, ["tenant-a", "tenant-b"])
