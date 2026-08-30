from __future__ import annotations

from typing import TYPE_CHECKING

from keycloak_admin_client.api.users import (
    get_admin_realms_realm_users,
    get_admin_realms_realm_users_user_id,
    put_admin_realms_realm_users_user_id,
)
from keycloak_admin_client.models.user_representation import UserRepresentation
from keycloak_admin_client.types import UNSET

from agentic_shared.integrations.idp.keycloak.errors import KeycloakAdminError
from agentic_shared.integrations.idp.keycloak.helpers import _check_response
from agentic_shared.integrations.idp.keycloak.user.mapping import to_record, with_tenant_memberships
from agentic_shared.integrations.idp.keycloak.user.models import UserRecord

if TYPE_CHECKING:
    from agentic_shared.integrations.idp.keycloak.user.gateway import UserGateway


class UserRepository:
    def __init__(self, gateway: UserGateway) -> None:
        self._gateway = gateway

    async def list_users(
        self,
        *,
        search: str | None = None,
        first: int = 0,
        max_results: int = 50,
    ) -> tuple[list[UserRecord], bool]:
        page_size = max(1, min(max_results, 200))
        client = await self._gateway._client()
        async with client:
            response = await get_admin_realms_realm_users.asyncio_detailed(
                self._gateway._realm,
                client=client,
                search=search if search else UNSET,
                first=max(0, first),
                max_=page_size,
                brief_representation=False,
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, list):
            return [], False
        records: list[UserRecord] = []
        for item in parsed:
            record = to_record(item)
            if record:
                records.append(await with_tenant_memberships(self._gateway, record))
        has_more = len(parsed) >= page_size
        return records, has_more

    async def get_by_username(self, username: str) -> UserRecord | None:
        client = await self._gateway._client()
        async with client:
            response = await get_admin_realms_realm_users.asyncio_detailed(
                self._gateway._realm,
                client=client,
                username=username,
                exact=True,
                max_=5,
                brief_representation=False,
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, list) or not parsed:
            return None
        record = to_record(parsed[0])
        if not record:
            return None
        return await with_tenant_memberships(self._gateway, record)

    async def get_representation(self, user_id: str) -> UserRepresentation:
        client = await self._gateway._client()
        async with client:
            response = await get_admin_realms_realm_users_user_id.asyncio_detailed(
                self._gateway._realm,
                user_id,
                client=client,
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, UserRepresentation):
            raise KeycloakAdminError(f"User not found: {user_id}")
        return parsed

    async def put_representation(self, body: UserRepresentation) -> None:
        user_id = body.id if body.id is not UNSET and body.id else None
        if not user_id:
            raise KeycloakAdminError("User id is required for update")
        client = await self._gateway._client()
        async with client:
            response = await put_admin_realms_realm_users_user_id.asyncio_detailed(
                self._gateway._realm,
                str(user_id),
                client=client,
                body=body,
            )
        _check_response(response.status_code, response.content)
