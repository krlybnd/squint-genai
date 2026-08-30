from __future__ import annotations

from keycloak_admin_client.models.user_representation import UserRepresentation
from keycloak_admin_client.models.user_representation_attributes import UserRepresentationAttributes

from agentic_shared.integrations.idp.keycloak.client import KeycloakAdminClientFactory
from agentic_shared.integrations.idp.keycloak.core.base import KeycloakGatewayBase
from agentic_shared.integrations.idp.keycloak.settings import KeycloakAdminSettings
from agentic_shared.integrations.idp.keycloak.tenant.gateway import TenantGateway
from agentic_shared.integrations.idp.keycloak.user.attributes import UserAttributes
from agentic_shared.integrations.idp.keycloak.user.create import create_user as _create_user
from agentic_shared.integrations.idp.keycloak.user.mapping import to_record
from agentic_shared.integrations.idp.keycloak.user.membership import UserTenantMembership
from agentic_shared.integrations.idp.keycloak.user.models import UserRecord
from agentic_shared.integrations.idp.keycloak.user.realm_roles import RealmRoles
from agentic_shared.integrations.idp.keycloak.user.repository import UserRepository
from agentic_shared.integrations.idp.keycloak.user.update import update_user as _update_user


class UserGateway(KeycloakGatewayBase):
    def __init__(
        self, settings: KeycloakAdminSettings, factory: KeycloakAdminClientFactory
    ) -> None:
        super().__init__(settings, factory)
        self._tenants = TenantGateway(settings, factory)
        self._repo = UserRepository(self)
        self._attrs = UserAttributes(self)
        self._realm_roles = RealmRoles(self)
        self._membership = UserTenantMembership(self)

    async def list_users(
        self,
        *,
        search: str | None = None,
        first: int = 0,
        max_results: int = 50,
    ) -> tuple[list[UserRecord], bool]:
        return await self._repo.list_users(search=search, first=first, max_results=max_results)

    async def get_by_username(self, username: str) -> UserRecord | None:
        return await self._repo.get_by_username(username)

    async def create_user(
        self,
        *,
        username: str,
        email: str | None,
        password: str,
        realm_roles: list[str] | None = None,
        enabled: bool = True,
    ) -> UserRecord:
        return await _create_user(
            self,
            username=username,
            email=email,
            password=password,
            realm_roles=realm_roles,
            enabled=enabled,
        )

    async def assign_tenant(
        self,
        username: str,
        tenant_alias: str,
        *,
        set_active: bool | None = None,
        roles: list[str] | None = None,
    ) -> UserRecord:
        return await self._membership.assign(
            username,
            tenant_alias,
            set_active=set_active,
            roles=roles,
        )

    async def set_tenant_roles(
        self, username: str, tenant_alias: str, roles: list[str]
    ) -> UserRecord:
        return await self._membership.set_roles(username, tenant_alias, roles)

    async def set_active_tenant(self, username: str, tenant_alias: str) -> UserRecord:
        return await self._membership.set_active(username, tenant_alias)

    async def remove_tenant(self, username: str) -> UserRecord:
        return await self._membership.remove_active(username)

    async def remove_from_tenant_org(self, username: str, tenant_alias: str) -> UserRecord:
        return await self._membership.remove_from_org(username, tenant_alias)

    async def update_user(
        self,
        username: str,
        *,
        email: str | None = None,
        enabled: bool | None = None,
        realm_roles: list[str] | None = None,
        tenant_alias: str | None = None,
        clear_tenant: bool = False,
        password: str | None = None,
    ) -> UserRecord:
        return await _update_user(
            self,
            username,
            email=email,
            enabled=enabled,
            realm_roles=realm_roles,
            tenant_alias=tenant_alias,
            clear_tenant=clear_tenant,
            password=password,
        )

    async def _get_user_representation(self, user_id: str) -> UserRepresentation:
        return await self._repo.get_representation(user_id)

    async def _put_user_representation(self, body: UserRepresentation) -> None:
        await self._repo.put_representation(body)

    async def _sync_realm_roles(self, user_id: str, desired_roles: list[str]) -> None:
        await self._realm_roles.sync(user_id, desired_roles)

    async def _put_user_attributes(
        self,
        user: UserRecord,
        *,
        tenant_id: str | None,
        tenant_roles: dict[str, list[str]],
    ) -> None:
        await self._attrs.put(user, tenant_id=tenant_id, tenant_roles=tenant_roles)

    def _to_record(self, user: UserRepresentation) -> UserRecord | None:
        return to_record(user)

    def _merged_tenant_attributes(
        self,
        existing: UserRepresentationAttributes | None,
        *,
        tenant_id: str | None,
        tenant_roles: dict[str, list[str]],
    ) -> UserRepresentationAttributes:
        return self._attrs._merged_tenant_attributes(
            existing,
            tenant_id=tenant_id,
            tenant_roles=tenant_roles,
        )
