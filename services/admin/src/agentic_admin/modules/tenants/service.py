import logging

from agentic_shared.integrations.keycloak_admin.errors import (
    KeycloakAdminError,
    KeycloakConflictError,
    KeycloakNotFoundError,
)
from agentic_shared.integrations.keycloak_admin.gateway import (
    TenantGateway,
    TenantMemberRecord,
    TenantRecord,
    UserGateway,
)

from agentic_admin.modules.tenants.schemas import TenantMemberOut, TenantOut

logger = logging.getLogger(__name__)


class TenantAdminService:
    def __init__(self, tenant_gateway: TenantGateway, user_gateway: UserGateway) -> None:
        self._tenants = tenant_gateway
        self._users = user_gateway

    @staticmethod
    def _out(record: TenantRecord) -> TenantOut:
        return TenantOut(
            id=record.id,
            alias=record.alias,
            name=record.name,
            enabled=record.enabled,
        )

    @staticmethod
    def _member_out(record: TenantMemberRecord) -> TenantMemberOut:
        return TenantMemberOut(
            id=record.id,
            username=record.username,
            email=record.email,
            roles=list(record.roles),
        )

    async def list_tenants(self) -> list[TenantOut]:
        records = await self._tenants.list_tenants()
        return [self._out(r) for r in records]

    async def create_tenant(self, *, alias: str, name: str) -> TenantOut:
        record = await self._tenants.create_tenant(alias=alias, name=name)
        logger.info("created tenant alias=%s id=%s", record.alias, record.id)
        return self._out(record)

    async def delete_tenant(self, alias: str) -> None:
        await self._tenants.delete_tenant(alias)
        logger.info("deleted tenant alias=%s", alias)

    async def update_tenant(self, alias: str, *, name: str, enabled: bool) -> TenantOut:
        record = await self._tenants.update_tenant(alias, name=name, enabled=enabled)
        logger.info("updated tenant alias=%s enabled=%s", record.alias, record.enabled)
        return self._out(record)

    async def list_members(
        self, alias: str, *, first: int = 0, max_results: int = 50
    ) -> tuple[list[TenantMemberOut], bool]:
        records, has_more = await self._tenants.list_members(
            alias, first=first, max_results=max_results
        )
        return [self._member_out(r) for r in records], has_more

    async def add_member(
        self, alias: str, username: str, *, roles: list[str] | None = None
    ) -> TenantMemberOut:
        await self._users.assign_tenant(username, alias, roles=roles)
        logger.info("added tenant member alias=%s username=%s roles=%s", alias, username, roles)
        members, _ = await self._tenants.list_members(alias, first=0, max_results=200)
        match = next((m for m in members if m.username == username), None)
        if not match:
            user = await self._users.get_by_username(username)
            if not user:
                raise KeycloakNotFoundError(f"User not found: {username}")
            return TenantMemberOut(
                id=user.id,
                username=user.username,
                email=user.email,
                roles=list(user.tenant_roles.get(alias, [])),
            )
        return self._member_out(match)

    async def update_member_roles(
        self, alias: str, username: str, roles: list[str]
    ) -> TenantMemberOut:
        user = await self._users.set_tenant_roles(username, alias, roles)
        logger.info(
            "updated tenant member roles alias=%s username=%s roles=%s",
            alias,
            username,
            roles,
        )
        return TenantMemberOut(
            id=user.id,
            username=user.username,
            email=user.email,
            roles=list(user.tenant_roles.get(alias, [])),
        )

    async def remove_member(self, alias: str, username: str) -> None:
        await self._users.remove_from_tenant_org(username, alias)
        logger.info("removed tenant member alias=%s username=%s", alias, username)


__all__ = [
    "KeycloakAdminError",
    "KeycloakConflictError",
    "KeycloakNotFoundError",
    "TenantAdminService",
]
