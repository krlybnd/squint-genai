from agentic_shared.integrations.idp.core import (
    IdpNotFoundError,
    UserTenancy,
    UserTenancyRead,
    UserTenancyWrite,
)

from agentic_api.modules.me.schemas import MembershipTenantOut, MeOut


class MeService:
    def __init__(self, reader: UserTenancyRead, writer: UserTenancyWrite) -> None:
        self._reader = reader
        self._writer = writer

    async def get_me(self, username: str) -> MeOut:
        tenancy = await self._reader.get(username)
        if tenancy is None:
            raise IdpNotFoundError(f"User not found: {username}")
        return self._to_out(tenancy)

    async def set_active_tenant(self, username: str, tenant_alias: str) -> MeOut:
        return self._to_out(await self._writer.set_active(username, tenant_alias))

    @staticmethod
    def _to_out(tenancy: UserTenancy) -> MeOut:
        return MeOut(
            username=tenancy.username,
            tenant_id=tenancy.tenant_id,
            tenants=[
                MembershipTenantOut(alias=tenant.alias, name=tenant.name)
                for tenant in tenancy.tenants
            ],
        )
