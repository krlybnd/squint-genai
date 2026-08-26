import json
import sys
import unittest
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch


def _install_keycloak_stubs() -> None:
    if "keycloak_admin_client" in sys.modules:
        return
    root = MagicMock(name="keycloak_admin_client")
    root.AuthenticatedClient = MagicMock
    sys.modules["keycloak_admin_client"] = root

    class _UserRepresentationAttributes:
        def __init__(self) -> None:
            self.additional_properties: dict = {}

        def __setitem__(self, key: str, value: object) -> None:
            self.additional_properties[key] = value

    class _UnsetType:
        pass

    unset = _UnsetType()

    submodule_names = [
        "api",
        "api.organizations",
        "api.role_mapper",
        "api.users",
        "models.credential_representation",
        "models.member_representation",
        "models.organization_domain_representation",
        "models.organization_representation",
        "models.role_representation",
        "models.user_representation",
        "models.user_representation_attributes",
        "types",
    ]
    for name in submodule_names:
        full_name = f"keycloak_admin_client.{name}"
        module = MagicMock(name=full_name)
        if name == "types":
            module.UNSET = unset
        if name == "models.user_representation_attributes":
            module.UserRepresentationAttributes = _UserRepresentationAttributes
        sys.modules[full_name] = module


_install_keycloak_stubs()

from agentic_shared.integrations.keycloak_admin.errors import (  # noqa: E402
    KeycloakAdminError,
    KeycloakConflictError,
    KeycloakForbiddenError,
    KeycloakNotFoundError,
)
from agentic_shared.integrations.keycloak_admin.gateway import (  # noqa: E402
    _check_response,
    _decode_error,
    _location_resource_id,
)


class TestKeycloakGatewayHelpers(unittest.TestCase):
    def test_location_resource_id_parses_trailing_segment(self) -> None:
        # Arrange
        headers = {
            "Location": "https://keycloak/admin/realms/demo/organizations/org-uuid-123",
        }

        # Act / Assert
        self.assertEqual(_location_resource_id(headers), "org-uuid-123")

    def test_location_resource_id_accepts_lowercase_header(self) -> None:
        # Arrange
        headers = {"location": "http://kc/users/user-42/"}

        # Act / Assert
        self.assertEqual(_location_resource_id(headers), "user-42")

    def test_location_resource_id_returns_none_when_missing(self) -> None:
        # Act / Assert
        self.assertIsNone(_location_resource_id({}))

    def test_decode_error_prefers_error_message_json_field(self) -> None:
        # Arrange
        content = json.dumps({"errorMessage": "User exists"}).encode()

        # Act / Assert
        self.assertEqual(_decode_error(content), "User exists")

    def test_decode_error_falls_back_to_error_field(self) -> None:
        # Arrange
        content = json.dumps({"error": "invalid_grant"}).encode()

        # Act / Assert
        self.assertEqual(_decode_error(content), "invalid_grant")

    def test_decode_error_empty_content(self) -> None:
        # Act / Assert
        self.assertEqual(_decode_error(b""), "Keycloak request failed")

    def test_decode_error_non_json_bytes(self) -> None:
        # Act / Assert
        self.assertEqual(_decode_error(b"plain text failure"), "plain text failure")

    def test_check_response_accepts_success_statuses(self) -> None:
        # Act / Assert
        for status in (HTTPStatus.OK, HTTPStatus.CREATED, HTTPStatus.NO_CONTENT):
            _check_response(status, b"")

    def test_check_response_raises_not_found(self) -> None:
        # Act / Assert
        with self.assertRaises(KeycloakNotFoundError):
            _check_response(HTTPStatus.NOT_FOUND, b'{"errorMessage":"missing"}')

    def test_check_response_raises_conflict(self) -> None:
        # Act / Assert
        with self.assertRaises(KeycloakConflictError):
            _check_response(HTTPStatus.CONFLICT, b'{"errorMessage":"exists"}')

    def test_check_response_raises_forbidden(self) -> None:
        # Act / Assert
        with self.assertRaises(KeycloakForbiddenError):
            _check_response(HTTPStatus.FORBIDDEN, b'{"errorMessage":"denied"}')

    def test_check_response_raises_generic_admin_error(self) -> None:
        # Act / Assert
        with self.assertRaises(KeycloakAdminError) as ctx:
            _check_response(HTTPStatus.BAD_REQUEST, b'{"errorMessage":"bad input"}')
        self.assertIn("400", str(ctx.exception))


class _ClientCtx:
    async def __aenter__(self) -> "_ClientCtx":
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


def _org(*, org_id: str = "org-1", alias: str = "acme", name: str = "Acme", enabled: bool = True):
    item = MagicMock()
    item.id = org_id
    item.alias = alias
    item.name = name
    item.enabled = enabled
    return item


def _http(
    *,
    status: HTTPStatus = HTTPStatus.OK,
    parsed: object = None,
    content: bytes = b"",
    headers: dict | None = None,
):
    response = MagicMock()
    response.status_code = status
    response.parsed = parsed
    response.content = content
    response.headers = headers or {}
    return response


class TestTenantGateway(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        from agentic_shared.integrations.keycloak_admin.gateway import TenantGateway
        from agentic_shared.integrations.keycloak_admin.settings import KeycloakAdminSettings

        self.factory = MagicMock()
        self.factory.authenticated_client = AsyncMock(return_value=_ClientCtx())
        self.gateway = TenantGateway(KeycloakAdminSettings(), self.factory)

    async def test_list_tenants_skips_incomplete_and_maps_records(self) -> None:
        # Arrange
        from keycloak_admin_client.types import UNSET

        from agentic_shared.integrations.keycloak_admin import gateway as gw

        incomplete = _org()
        incomplete.id = UNSET

        # Act
        with patch.object(
            gw.get_admin_realms_realm_organizations,
            "asyncio_detailed",
            new=AsyncMock(return_value=_http(parsed=[incomplete, _org()])),
        ):
            records = await self.gateway.list_tenants()

        # Assert
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].alias, "acme")

    async def test_list_tenants_empty_when_parsed_is_not_a_list(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin import gateway as gw

        # Act / Assert
        with patch.object(
            gw.get_admin_realms_realm_organizations,
            "asyncio_detailed",
            new=AsyncMock(return_value=_http(parsed={"oops": True})),
        ):
            self.assertEqual(await self.gateway.list_tenants(), [])

    async def test_get_by_alias_returns_none_when_missing(self) -> None:
        # Arrange
        self.gateway.list_tenants = AsyncMock(return_value=[])  # type: ignore[method-assign]

        # Act / Assert
        self.assertIsNone(await self.gateway.get_by_alias("missing"))

    async def test_create_tenant_conflict_when_alias_exists(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin.errors import KeycloakConflictError
        from agentic_shared.integrations.keycloak_admin.gateway import TenantRecord

        self.gateway.get_by_alias = AsyncMock(  # type: ignore[method-assign]
            return_value=TenantRecord(id="1", alias="acme", name="Acme", enabled=True),
        )

        # Act / Assert
        with self.assertRaises(KeycloakConflictError):
            await self.gateway.create_tenant(alias="acme", name="Acme")

    async def test_create_tenant_uses_location_header(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin import gateway as gw

        self.gateway.get_by_alias = AsyncMock(return_value=None)  # type: ignore[method-assign]

        # Act
        with patch.object(
            gw.post_admin_realms_realm_organizations,
            "asyncio_detailed",
            new=AsyncMock(
                return_value=_http(
                    status=HTTPStatus.CREATED,
                    headers={"Location": "https://kc/organizations/new-id"},
                ),
            ),
        ):
            created = await self.gateway.create_tenant(alias="acme", name="Acme")

        # Assert
        self.assertEqual(created.id, "new-id")
        self.assertEqual(created.alias, "acme")

    async def test_delete_tenant_raises_when_missing(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin.errors import KeycloakNotFoundError

        self.gateway.get_by_alias = AsyncMock(return_value=None)  # type: ignore[method-assign]

        # Act / Assert
        with self.assertRaises(KeycloakNotFoundError):
            await self.gateway.delete_tenant("missing")

    async def test_delete_tenant_calls_keycloak(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin import gateway as gw
        from agentic_shared.integrations.keycloak_admin.gateway import TenantRecord

        self.gateway.get_by_alias = AsyncMock(  # type: ignore[method-assign]
            return_value=TenantRecord(id="org-1", alias="acme", name="Acme", enabled=True),
        )

        # Act
        with patch.object(
            gw.delete_admin_realms_realm_organizations_org_id,
            "asyncio_detailed",
            new=AsyncMock(return_value=_http(status=HTTPStatus.NO_CONTENT)),
        ) as delete:
            await self.gateway.delete_tenant("acme")

        # Assert
        delete.assert_awaited_once()


class TestUserGateway(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        from agentic_shared.integrations.keycloak_admin.gateway import UserGateway
        from agentic_shared.integrations.keycloak_admin.settings import KeycloakAdminSettings

        self.factory = MagicMock()
        self.factory.authenticated_client = AsyncMock(return_value=_ClientCtx())
        self.gateway = UserGateway(KeycloakAdminSettings(), self.factory)

    def test_to_record_requires_id_and_username(self) -> None:
        # Arrange
        from keycloak_admin_client.types import UNSET

        user = MagicMock()
        user.id = UNSET
        user.username = "alice"

        # Act / Assert
        self.assertIsNone(self.gateway._to_record(user))

    def test_to_record_maps_attributes_and_roles(self) -> None:
        # Arrange
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

        # Act
        record = self.gateway._to_record(user)

        # Assert
        assert record is not None
        self.assertEqual(record.tenant_id, "acme")
        self.assertEqual(record.realm_roles, ["read", "write"])

    async def test_get_by_username_returns_none_when_empty(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin import gateway as gw

        # Act / Assert
        with patch.object(
            gw.get_admin_realms_realm_users,
            "asyncio_detailed",
            new=AsyncMock(return_value=_http(parsed=[])),
        ):
            self.assertIsNone(await self.gateway.get_by_username("missing"))

    async def test_create_user_conflict_when_username_exists(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin.errors import KeycloakConflictError
        from agentic_shared.integrations.keycloak_admin.gateway import UserRecord

        self.gateway.get_by_username = AsyncMock(  # type: ignore[method-assign]
            return_value=UserRecord(
                id="u1",
                username="alice",
                email=None,
                enabled=True,
                tenant_id=None,
                tenant_ids=[],
                realm_roles=[],
            ),
        )

        # Act / Assert
        with self.assertRaises(KeycloakConflictError):
            await self.gateway.create_user(username="alice", email=None, password="x")

    async def test_assign_tenant_raises_when_user_missing(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin.errors import KeycloakNotFoundError

        self.gateway.get_by_username = AsyncMock(return_value=None)  # type: ignore[method-assign]

        # Act / Assert
        with self.assertRaises(KeycloakNotFoundError):
            await self.gateway.assign_tenant("alice", "acme")


class TestKeycloakAdminClientFactory(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_token_posts_client_credentials(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin.client import KeycloakAdminClientFactory
        from agentic_shared.integrations.keycloak_admin.settings import KeycloakAdminSettings

        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {"access_token": "tok-1"}
        http = MagicMock()
        http.post = AsyncMock(return_value=response)
        http.__aenter__ = AsyncMock(return_value=http)
        http.__aexit__ = AsyncMock(return_value=None)

        # Act
        with patch(
            "agentic_shared.integrations.keycloak_admin.client.httpx.AsyncClient",
            return_value=http,
        ):
            factory = KeycloakAdminClientFactory(KeycloakAdminSettings())
            token = await factory.fetch_token()

        # Assert
        self.assertEqual(token, "tok-1")
        http.post.assert_awaited_once()
        kwargs = http.post.await_args.kwargs
        self.assertEqual(kwargs["data"]["grant_type"], "client_credentials")

    async def test_fetch_token_rejects_missing_access_token(self) -> None:
        # Arrange
        from agentic_shared.integrations.keycloak_admin.client import KeycloakAdminClientFactory
        from agentic_shared.integrations.keycloak_admin.settings import KeycloakAdminSettings

        response = MagicMock()
        response.raise_for_status = MagicMock()
        response.json.return_value = {}
        http = MagicMock()
        http.post = AsyncMock(return_value=response)
        http.__aenter__ = AsyncMock(return_value=http)
        http.__aexit__ = AsyncMock(return_value=None)

        # Act / Assert
        with patch(
            "agentic_shared.integrations.keycloak_admin.client.httpx.AsyncClient",
            return_value=http,
        ):
            factory = KeycloakAdminClientFactory(KeycloakAdminSettings())
            with self.assertRaises(RuntimeError):
                await factory.fetch_token()


if __name__ == "__main__":
    unittest.main()
