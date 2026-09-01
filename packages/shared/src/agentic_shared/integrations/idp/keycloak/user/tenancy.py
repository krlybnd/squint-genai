from agentic_shared.integrations.idp.core.errors import IdpForbiddenError, IdpNotFoundError
from agentic_shared.integrations.idp.core.protocols import UserAdmin
from agentic_shared.integrations.idp.core.records import TenantRecord, UserTenancy


class KeycloakUserTenancy:
    """Api tenancy: user record only — never list Organizations (needs manage-realm on KC 26)."""

    def __init__(self, users: UserAdmin) -> None:
        self._users = users

    async def get(self, username: str) -> UserTenancy | None:
        record = await self._users.get_by_username(username)
        if record is None:
            return None
        tenants = [
            TenantRecord(
                id=alias,
                alias=alias,
                name=record.tenant_labels.get(alias, alias),
                enabled=True,
            )
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
