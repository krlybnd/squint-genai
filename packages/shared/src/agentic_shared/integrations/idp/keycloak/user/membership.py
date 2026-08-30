from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from keycloak_admin_client.api.organizations import (
    delete_admin_realms_realm_organizations_org_id_members_member_id,
    post_admin_realms_realm_organizations_org_id_members,
)

from agentic_shared.integrations.idp.keycloak.errors import (
    KeycloakAdminError,
    KeycloakNotFoundError,
)
from agentic_shared.integrations.idp.keycloak.helpers import _check_response, _normalize_roles
from agentic_shared.integrations.idp.keycloak.user.models import UserRecord

if TYPE_CHECKING:
    from agentic_shared.integrations.idp.keycloak.user.gateway import UserGateway


class UserTenantMembership:
    def __init__(self, gateway: UserGateway) -> None:
        self._gateway = gateway

    async def assign(
        self,
        username: str,
        tenant_alias: str,
        *,
        set_active: bool | None = None,
        roles: list[str] | None = None,
    ) -> UserRecord:
        user = await self._gateway.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")
        tenant = await self._gateway._tenants.get_by_alias(tenant_alias)
        if not tenant:
            raise KeycloakNotFoundError(f"Tenant not found: {tenant_alias}")

        client = await self._gateway._client()
        async with client:
            response = await post_admin_realms_realm_organizations_org_id_members.asyncio_detailed(
                self._gateway._realm,
                tenant.id,
                client=client,
                body=user.id,
            )
        if response.status_code not in (HTTPStatus.CREATED, HTTPStatus.CONFLICT):
            _check_response(response.status_code, response.content)

        tenant_roles = dict(user.tenant_roles)
        if roles is not None:
            tenant_roles[tenant_alias] = _normalize_roles(roles)
        elif tenant_alias not in tenant_roles:
            tenant_roles[tenant_alias] = []

        should_set_active = set_active if set_active is not None else user.tenant_id is None
        active = tenant_alias if should_set_active else user.tenant_id
        await self._gateway._attrs.put(user, tenant_id=active, tenant_roles=tenant_roles)
        await self._gateway._realm_roles.sync_active_tenant(
            user.id,
            tenant_id=active,
            tenant_roles=tenant_roles,
        )

        refreshed = await self._gateway.get_by_username(username)
        if not refreshed:
            raise KeycloakAdminError("User tenant assignment failed")
        return refreshed

    async def set_roles(self, username: str, tenant_alias: str, roles: list[str]) -> UserRecord:
        user = await self._gateway.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")
        if tenant_alias not in user.tenant_ids:
            raise KeycloakNotFoundError(f"User is not a member of tenant: {tenant_alias}")

        tenant_roles = dict(user.tenant_roles)
        tenant_roles[tenant_alias] = _normalize_roles(roles)
        await self._gateway._attrs.put(
            user,
            tenant_id=user.tenant_id,
            tenant_roles=tenant_roles,
        )
        await self._gateway._realm_roles.sync_active_tenant(
            user.id,
            tenant_id=user.tenant_id,
            tenant_roles=tenant_roles,
        )

        refreshed = await self._gateway.get_by_username(username)
        if not refreshed:
            raise KeycloakAdminError("Tenant role update failed")
        return refreshed

    async def set_active(self, username: str, tenant_alias: str) -> UserRecord:
        user = await self._gateway.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")
        if tenant_alias not in user.tenant_ids:
            raise KeycloakNotFoundError(f"User is not a member of tenant: {tenant_alias}")
        await self._gateway._attrs.put(
            user,
            tenant_id=tenant_alias,
            tenant_roles=dict(user.tenant_roles),
        )
        await self._gateway._realm_roles.sync_active_tenant(
            user.id,
            tenant_id=tenant_alias,
            tenant_roles=user.tenant_roles,
        )
        refreshed = await self._gateway.get_by_username(username)
        if not refreshed:
            raise KeycloakAdminError("Active tenant update failed")
        return refreshed

    async def remove_active(self, username: str) -> UserRecord:
        user = await self._gateway.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")
        if not user.tenant_id:
            return user
        return await self.remove_from_org(username, user.tenant_id)

    async def remove_from_org(self, username: str, tenant_alias: str) -> UserRecord:
        user = await self._gateway.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")
        tenant = await self._gateway._tenants.get_by_alias(tenant_alias)
        if not tenant:
            raise KeycloakNotFoundError(f"Tenant not found: {tenant_alias}")

        client = await self._gateway._client()
        async with client:
            remove_member = (
                delete_admin_realms_realm_organizations_org_id_members_member_id.asyncio_detailed
            )
            response = await remove_member(
                self._gateway._realm,
                tenant.id,
                user.id,
                client=client,
            )
        if response.status_code not in (HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND):
            _check_response(response.status_code, response.content)

        remaining = [a for a in user.tenant_ids if a != tenant_alias]
        tenant_roles = {
            alias: roles for alias, roles in user.tenant_roles.items() if alias != tenant_alias
        }
        if user.tenant_id == tenant_alias:
            new_active = remaining[0] if remaining else None
        else:
            new_active = user.tenant_id
        await self._gateway._attrs.put(user, tenant_id=new_active, tenant_roles=tenant_roles)
        await self._gateway._realm_roles.sync_active_tenant(
            user.id,
            tenant_id=new_active,
            tenant_roles=tenant_roles,
        )

        refreshed = await self._gateway.get_by_username(username)
        if not refreshed:
            raise KeycloakAdminError("User tenant removal failed")
        return refreshed
