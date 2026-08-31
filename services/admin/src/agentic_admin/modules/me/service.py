from agentic_shared.integrations.idp.core import (
    IdpForbiddenError,
    IdpNotFoundError,
    TenantAdmin,
    UserAdmin,
)

from agentic_admin.modules.me.schemas import MembershipTenantOut, MeOut


class MeService:
    def __init__(self, users: UserAdmin, tenants: TenantAdmin) -> None:
        self._users = users
        self._tenants = tenants

    async def get_me(self, username: str) -> MeOut:
        record = await self._users.get_by_username(username)
        if not record:
            raise IdpNotFoundError(f"User not found: {username}")
        names = await self._tenant_names(record.tenant_ids)
        return MeOut(
            username=record.username,
            tenant_id=record.tenant_id,
            tenants=[
                MembershipTenantOut(alias=alias, name=names.get(alias, alias))
                for alias in record.tenant_ids
            ],
        )

    async def set_active_tenant(self, username: str, tenant_alias: str) -> MeOut:
        record = await self._users.get_by_username(username)
        if not record:
            raise IdpNotFoundError(f"User not found: {username}")
        if tenant_alias not in record.tenant_ids:
            raise IdpForbiddenError(f"Not a member of tenant: {tenant_alias}")
        await self._users.set_active_tenant(username, tenant_alias)
        return await self.get_me(username)

    async def _tenant_names(self, aliases: list[str]) -> dict[str, str]:
        if not aliases:
            return {}
        orgs = await self._tenants.list_tenants()
        return {org.alias: org.name for org in orgs if org.alias in set(aliases)}
