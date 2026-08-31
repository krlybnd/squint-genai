from agentic_shared.integrations.idp.core.errors import IdpForbiddenError, IdpNotFoundError
from agentic_shared.integrations.idp.core.protocols import TenantAdmin, UserAdmin
from agentic_shared.integrations.idp.core.records import TenantRecord, UserTenancy


class KeycloakUserTenancy:
    def __init__(self, users: UserAdmin, tenants: TenantAdmin) -> None:
        self._users = users
        self._tenants = tenants

    async def get(self, username: str) -> UserTenancy | None:
        record = await self._users.get_by_username(username)
        if record is None:
            return None
        catalog = {org.alias: org for org in await self._tenants.list_tenants()}
        tenants = [
            catalog.get(alias, TenantRecord(id=alias, alias=alias, name=alias, enabled=True))
            for alias in record.tenant_ids
        ]
        return UserTenancy(
            username=record.username,
            tenant_id=record.tenant_id,
            tenants=tenants,
        )

    async def set_active(self, username: str, tenant_alias: str) -> UserTenancy:
        current = await self.get(username)
        if current is None:
            raise IdpNotFoundError(f"User not found: {username}")
        if tenant_alias not in {tenant.alias for tenant in current.tenants}:
            raise IdpForbiddenError(f"Not a member of tenant: {tenant_alias}")
        await self._users.set_active_tenant(username, tenant_alias)
        refreshed = await self.get(username)
        if refreshed is None:
            raise IdpNotFoundError(f"User not found: {username}")
        return refreshed
