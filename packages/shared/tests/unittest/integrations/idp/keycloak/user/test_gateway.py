from __future__ import annotations

import json
import sys
import unittest
from http import HTTPStatus
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from support import ClientCtx, http_response  # noqa: E402


class TestUserGateway(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        from agentic_shared.integrations.idp.keycloak import UserGateway
        from agentic_shared.integrations.idp.keycloak.settings import KeycloakAdminSettings

        self.factory = MagicMock()
        self.factory.authenticated_client = AsyncMock(return_value=ClientCtx())
        self.gateway = UserGateway(KeycloakAdminSettings(), self.factory)

    def test_to_record_requires_id_and_username(self) -> None:
        from keycloak_admin_client.types import UNSET

        user = MagicMock()
        user.id = UNSET
        user.username = "alice"
        self.assertIsNone(self.gateway._to_record(user))

    def test_to_record_maps_attributes_and_roles(self) -> None:
        from keycloak_admin_client.models.user_representation_attributes import (
            UserRepresentationAttributes,
        )

        attrs = UserRepresentationAttributes()
        attrs.additional_properties = {"tenant_id": ["acme"]}
        user = MagicMock()
        user.id = "u1"
        user.username = "alice"
        user.email = "alice@example.com"
        user.enabled = True
        user.attributes = attrs
        user.realm_roles = ["read", "write"]

        record = self.gateway._to_record(user)

        assert record is not None
        self.assertEqual(record.tenant_id, "acme")
        self.assertEqual(record.realm_roles, ["read", "write"])
        self.assertEqual(record.tenant_roles, {})

    def test_to_record_parses_tenant_roles_attribute(self) -> None:
        from keycloak_admin_client.models.user_representation_attributes import (
            UserRepresentationAttributes,
        )

        attrs = UserRepresentationAttributes()
        attrs.additional_properties = {
            "tenant_id": ["acme"],
            "tenant_roles": [json.dumps({"acme": ["read", "admin"], "other": ["write"]})],
        }
        user = MagicMock()
        user.id = "u1"
        user.username = "alice"
        user.email = None
        user.enabled = True
        user.attributes = attrs
        user.realm_roles = []

        record = self.gateway._to_record(user)

        assert record is not None
        self.assertEqual(record.tenant_roles["acme"], ["admin", "read"])
        self.assertEqual(record.realm_roles, ["admin", "read"])

    def test_merged_tenant_attributes_preserves_other_keys(self) -> None:
        from keycloak_admin_client.models.user_representation_attributes import (
            UserRepresentationAttributes,
        )

        attrs = UserRepresentationAttributes()
        attrs.additional_properties = {
            "locale": ["en"],
            "tenant_id": ["old"],
            "tenant_roles": ['{"old":["read"]}'],
        }

        merged = self.gateway._merged_tenant_attributes(
            attrs,
            tenant_id="acme",
            tenant_roles={"acme": ["write"]},
        )

        self.assertEqual(merged.additional_properties["locale"], ["en"])
        self.assertEqual(merged.additional_properties["tenant_id"], ["acme"])
        stored = json.loads(merged.additional_properties["tenant_roles"][0])
        self.assertEqual(stored, {"acme": ["write"]})

    async def test_put_user_attributes_preserves_profile_fields(self) -> None:
        from keycloak_admin_client.models.user_representation_attributes import (
            UserRepresentationAttributes,
        )

        from agentic_shared.integrations.idp.keycloak import UserRecord

        attrs = UserRepresentationAttributes()
        attrs.additional_properties = {"locale": ["en"]}
        rep = MagicMock()
        rep.id = "u1"
        rep.username = "alice"
        rep.email = "alice@example.com"
        rep.first_name = "Alice"
        rep.last_name = "TenantA"
        rep.enabled = True
        rep.attributes = attrs
        user = UserRecord(
            id="u1",
            username="alice",
            email="alice@example.com",
            enabled=True,
            tenant_id="tenant-a",
            tenant_ids=["tenant-a"],
            realm_roles=["read"],
            tenant_roles={},
        )
        self.gateway._get_user_representation = AsyncMock(return_value=rep)  # type: ignore[method-assign]
        self.gateway._put_user_representation = AsyncMock()  # type: ignore[method-assign]

        await self.gateway._put_user_attributes(
            user,
            tenant_id="tenant-a",
            tenant_roles={"tenant-a": ["write"]},
        )

        self.gateway._put_user_representation.assert_awaited_once()
        sent = self.gateway._put_user_representation.await_args.args[0]
        self.assertEqual(sent.email, "alice@example.com")
        self.assertEqual(sent.first_name, "Alice")
        self.assertEqual(sent.last_name, "TenantA")
        merged_attrs = sent.attributes.additional_properties
        self.assertEqual(merged_attrs["locale"], ["en"])
        self.assertEqual(merged_attrs["tenant_id"], ["tenant-a"])
        self.assertEqual(json.loads(merged_attrs["tenant_roles"][0]), {"tenant-a": ["write"]})

    async def test_set_tenant_roles_requires_membership(self) -> None:
        from agentic_shared.integrations.idp.keycloak import UserRecord
        from agentic_shared.integrations.idp.keycloak.errors import KeycloakNotFoundError

        self.gateway.get_by_username = AsyncMock(  # type: ignore[method-assign]
            return_value=UserRecord(
                id="u1",
                username="alice",
                email="alice@example.com",
                enabled=True,
                tenant_id="tenant-a",
                tenant_ids=["tenant-a"],
                realm_roles=["read"],
                tenant_roles={"tenant-a": ["read"]},
            )
        )

        with self.assertRaises(KeycloakNotFoundError):
            await self.gateway.set_tenant_roles("alice", "missing", ["write"])

    async def test_sync_realm_roles_resolves_role_ids(self) -> None:
        from keycloak_admin_client.models.role_representation import RoleRepresentation
        from keycloak_admin_client.types import UNSET

        import agentic_shared.integrations.idp.keycloak as kc

        current = RoleRepresentation(id="id-read", name="read")
        role_read = RoleRepresentation(id="id-read", name="read")
        role_write = RoleRepresentation(id="id-write", name="write")
        self.assertIsNot(current.id, UNSET)

        with (
            patch.object(
                kc.get_admin_realms_realm_users_user_id_role_mappings_realm,
                "asyncio_detailed",
                new=AsyncMock(return_value=http_response(parsed=[current])),
            ),
            patch.object(
                kc.get_admin_realms_realm_roles_role_name,
                "asyncio_detailed",
                new=AsyncMock(
                    side_effect=[
                        http_response(parsed=role_read),
                        http_response(parsed=role_write),
                    ]
                ),
            ) as get_role,
            patch.object(
                kc.delete_admin_realms_realm_users_user_id_role_mappings_realm,
                "asyncio_detailed",
                new=AsyncMock(return_value=http_response(status=HTTPStatus.NO_CONTENT)),
            ) as delete_roles,
            patch.object(
                kc.post_admin_realms_realm_users_user_id_role_mappings_realm,
                "asyncio_detailed",
                new=AsyncMock(return_value=http_response(status=HTTPStatus.NO_CONTENT)),
            ) as add_roles,
        ):
            await self.gateway._sync_realm_roles("u1", ["write"])

        delete_roles.assert_awaited_once()
        add_roles.assert_awaited_once()
        self.assertEqual(get_role.await_count, 2)

    async def test_get_by_username_returns_none_when_empty(self) -> None:
        import agentic_shared.integrations.idp.keycloak as kc

        with patch.object(
            kc.get_admin_realms_realm_users,
            "asyncio_detailed",
            new=AsyncMock(return_value=http_response(parsed=[])),
        ):
            self.assertIsNone(await self.gateway.get_by_username("missing"))

    async def test_create_user_conflict_when_username_exists(self) -> None:
        from agentic_shared.integrations.idp.keycloak import UserRecord
        from agentic_shared.integrations.idp.keycloak.errors import KeycloakConflictError

        self.gateway.get_by_username = AsyncMock(  # type: ignore[method-assign]
            return_value=UserRecord(
                id="u1",
                username="alice",
                email=None,
                enabled=True,
                tenant_id=None,
                tenant_ids=[],
                realm_roles=[],
                tenant_roles={},
            ),
        )

        with self.assertRaises(KeycloakConflictError):
            await self.gateway.create_user(username="alice", email=None, password="x")

    async def test_assign_tenant_raises_when_user_missing(self) -> None:
        from agentic_shared.integrations.idp.keycloak.errors import KeycloakNotFoundError

        self.gateway.get_by_username = AsyncMock(return_value=None)  # type: ignore[method-assign]

        with self.assertRaises(KeycloakNotFoundError):
            await self.gateway.assign_tenant("alice", "acme")
