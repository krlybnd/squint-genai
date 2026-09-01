from __future__ import annotations

from typing import TYPE_CHECKING

from keycloak_admin_client.api.organizations import (
    get_admin_realms_realm_organizations_members_member_id_organizations as get_member_orgs,
)
from keycloak_admin_client.api.organizations import (
    get_admin_realms_realm_organizations_org_id_members,
)
from keycloak_admin_client.types import UNSET

from agentic_shared.integrations.idp.keycloak.errors import KeycloakNotFoundError
from agentic_shared.integrations.idp.keycloak.helpers import _check_response, _roles_for_tenant
from agentic_shared.integrations.idp.keycloak.tenant.models import TenantMemberRecord, TenantRecord

if TYPE_CHECKING:
    from agentic_shared.integrations.idp.keycloak.tenant.gateway import TenantGateway


class TenantMembers:
    def __init__(self, gateway: TenantGateway) -> None:
        self._gateway = gateway

    async def list_members(
        self,
        alias: str,
        *,
        first: int = 0,
        max_results: int = 50,
    ) -> tuple[list[TenantMemberRecord], bool]:
        tenant = await self._gateway.get_by_alias(alias)
        if not tenant:
            raise KeycloakNotFoundError(f"Tenant not found: {alias}")
        page_size = max(1, min(max_results, 200))
        client = await self._gateway._client()
        async with client:
            response = await get_admin_realms_realm_organizations_org_id_members.asyncio_detailed(
                self._gateway._realm,
                tenant.id,
                client=client,
                first=max(0, first),
                max_=page_size,
                brief_representation=False,
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, list):
            return [], False
        members: list[TenantMemberRecord] = []
        import agentic_shared.integrations.idp.keycloak as _kc

        for item in parsed:
            if not isinstance(item, _kc.MemberRepresentation):
                continue
            user_id = item.id if item.id is not UNSET and item.id else None
            username = item.username if item.username is not UNSET and item.username else None
            if not user_id or not username or str(username).startswith("service-account-"):
                continue
            email = item.email if item.email is not UNSET and item.email else None
            tenant_roles = await self._gateway._fetch_user_tenant_roles(str(user_id))
            members.append(
                TenantMemberRecord(
                    id=str(user_id),
                    username=str(username),
                    email=str(email) if email else None,
                    roles=_roles_for_tenant(tenant_roles, alias),
                )
            )
        has_more = len(parsed) >= page_size
        return members, has_more

    async def list_tenants_for_user(self, user_id: str) -> list[TenantRecord]:
        # Per-user orgs: view-users is enough. GET /organizations needs manage-realm on KC 26.
        client = await self._gateway._client()
        async with client:
            response = await get_member_orgs.asyncio_detailed(
                self._gateway._realm,
                user_id,
                client=client,
                brief_representation=False,
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, list):
            return []
        records: list[TenantRecord] = []
        for item in parsed:
            record = self._gateway._to_record(item)
            if record:
                records.append(record)
        return sorted(records, key=lambda item: item.alias)

    async def list_tenant_aliases_for_user(self, user_id: str) -> list[str]:
        return [record.alias for record in await self.list_tenants_for_user(user_id)]
