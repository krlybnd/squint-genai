from __future__ import annotations

from typing import TYPE_CHECKING

from keycloak_admin_client.api.role_mapper import (
    delete_admin_realms_realm_users_user_id_role_mappings_realm,
    get_admin_realms_realm_users_user_id_role_mappings_realm,
    post_admin_realms_realm_users_user_id_role_mappings_realm,
)
from keycloak_admin_client.api.roles import get_admin_realms_realm_roles_role_name
from keycloak_admin_client.models.role_representation import RoleRepresentation
from keycloak_admin_client.types import UNSET

from agentic_shared.integrations.idp.keycloak.errors import KeycloakAdminError
from agentic_shared.integrations.idp.keycloak.helpers import (
    _APP_REALM_ROLES,
    _check_response,
    _normalize_roles,
)

if TYPE_CHECKING:
    from agentic_shared.integrations.idp.keycloak.user.gateway import UserGateway


class RealmRoles:
    def __init__(self, gateway: UserGateway) -> None:
        self._gateway = gateway

    async def _resolve(self, role_names: list[str]) -> list[RoleRepresentation]:
        resolved: list[RoleRepresentation] = []
        client = await self._gateway._client()
        async with client:
            for name in role_names:
                response = await get_admin_realms_realm_roles_role_name.asyncio_detailed(
                    self._gateway._realm,
                    name,
                    client=client,
                )
                _check_response(response.status_code, response.content)
                role = response.parsed
                if not isinstance(role, RoleRepresentation):
                    raise KeycloakAdminError(f"Realm role not found: {name}")
                role_id = role.id if role.id is not UNSET and role.id else None
                role_name = role.name if role.name is not UNSET and role.name else name
                if not role_id:
                    raise KeycloakAdminError(f"Realm role missing id: {name}")
                resolved.append(RoleRepresentation(id=str(role_id), name=str(role_name)))
        return resolved

    async def _list_user_role_names(self, user_id: str) -> set[str]:
        client = await self._gateway._client()
        async with client:
            response = (
                await get_admin_realms_realm_users_user_id_role_mappings_realm.asyncio_detailed(
                    self._gateway._realm,
                    user_id,
                    client=client,
                )
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, list):
            return set()
        names: set[str] = set()
        for role in parsed:
            if not isinstance(role, RoleRepresentation):
                continue
            name = role.name if role.name is not UNSET and role.name else None
            if name and str(name) in _APP_REALM_ROLES:
                names.add(str(name))
        return names

    async def sync(self, user_id: str, desired_roles: list[str]) -> None:
        desired = set(_normalize_roles(desired_roles))
        current = await self._list_user_role_names(user_id)
        to_remove = current - desired
        to_add = desired - current
        if to_remove:
            body = await self._resolve(sorted(to_remove))
            client = await self._gateway._client()
            async with client:
                delete_roles = (
                    delete_admin_realms_realm_users_user_id_role_mappings_realm.asyncio_detailed
                )
                response = await delete_roles(
                    self._gateway._realm,
                    user_id,
                    client=client,
                    body=body,
                )
            _check_response(response.status_code, response.content)
        if to_add:
            body = await self._resolve(sorted(to_add))
            client = await self._gateway._client()
            async with client:
                add_roles = (
                    post_admin_realms_realm_users_user_id_role_mappings_realm.asyncio_detailed
                )
                response = await add_roles(
                    self._gateway._realm,
                    user_id,
                    client=client,
                    body=body,
                )
            _check_response(response.status_code, response.content)

    async def sync_active_tenant(
        self,
        user_id: str,
        *,
        tenant_id: str | None,
        tenant_roles: dict[str, list[str]],
    ) -> None:
        if tenant_id:
            await self.sync(user_id, tenant_roles.get(tenant_id, []))
        else:
            await self.sync(user_id, [])
