from __future__ import annotations

from http import HTTPStatus

from keycloak_admin_client.api.organizations import (
    delete_admin_realms_realm_organizations_org_id,
    get_admin_realms_realm_organizations,
    post_admin_realms_realm_organizations,
    put_admin_realms_realm_organizations_org_id,
)
from keycloak_admin_client.api.users import get_admin_realms_realm_users_user_id
from keycloak_admin_client.models.organization_domain_representation import (
    OrganizationDomainRepresentation,
)
from keycloak_admin_client.models.organization_representation import OrganizationRepresentation
from keycloak_admin_client.models.user_representation import UserRepresentation
from keycloak_admin_client.models.user_representation_attributes import UserRepresentationAttributes
from keycloak_admin_client.types import UNSET

from agentic_shared.integrations.idp.keycloak.client import KeycloakAdminClientFactory
from agentic_shared.integrations.idp.keycloak.core.base import KeycloakGatewayBase
from agentic_shared.integrations.idp.keycloak.errors import (
    KeycloakAdminError,
    KeycloakConflictError,
    KeycloakNotFoundError,
)
from agentic_shared.integrations.idp.keycloak.helpers import (
    _check_response,
    _location_resource_id,
    _parse_tenant_roles,
)
from agentic_shared.integrations.idp.keycloak.settings import KeycloakAdminSettings
from agentic_shared.integrations.idp.keycloak.tenant.members import TenantMembers
from agentic_shared.integrations.idp.keycloak.tenant.models import TenantMemberRecord, TenantRecord


class TenantGateway(KeycloakGatewayBase):
    def __init__(
        self, settings: KeycloakAdminSettings, factory: KeycloakAdminClientFactory
    ) -> None:
        super().__init__(settings, factory)
        self._members = TenantMembers(self)

    def _to_record(self, org: OrganizationRepresentation) -> TenantRecord | None:
        org_id = org.id if org.id is not UNSET and org.id else None
        alias = org.alias if org.alias is not UNSET and org.alias else None
        name = org.name if org.name is not UNSET and org.name else None
        if not org_id or not alias:
            return None
        enabled = bool(org.enabled) if org.enabled is not UNSET else True
        return TenantRecord(
            id=str(org_id), alias=str(alias), name=str(name or alias), enabled=enabled
        )

    async def list_tenants(self) -> list[TenantRecord]:
        client = await self._client()
        async with client:
            response = await get_admin_realms_realm_organizations.asyncio_detailed(
                self._realm,
                client=client,
                max_=500,
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, list):
            return []
        records: list[TenantRecord] = []
        for item in parsed:
            record = self._to_record(item)
            if record:
                records.append(record)
        return records

    async def get_by_alias(self, alias: str) -> TenantRecord | None:
        for record in await self.list_tenants():
            if record.alias == alias:
                return record
        return None

    async def create_tenant(self, *, alias: str, name: str) -> TenantRecord:
        existing = await self.get_by_alias(alias)
        if existing:
            raise KeycloakConflictError(f"Tenant alias already exists: {alias}")

        body = OrganizationRepresentation(
            name=name,
            alias=alias,
            enabled=True,
            domains=[OrganizationDomainRepresentation(name=f"{alias}.local")],
        )
        client = await self._client()
        async with client:
            response = await post_admin_realms_realm_organizations.asyncio_detailed(
                self._realm,
                client=client,
                body=body,
            )
        if response.status_code == HTTPStatus.CONFLICT:
            raise KeycloakConflictError(f"Tenant alias already exists: {alias}")
        _check_response(response.status_code, response.content)

        org_id = _location_resource_id(dict(response.headers))
        if org_id:
            return TenantRecord(id=org_id, alias=alias, name=name, enabled=True)
        created = await self.get_by_alias(alias)
        if not created:
            raise KeycloakAdminError("Organization created but could not be resolved")
        return created

    async def delete_tenant(self, alias: str) -> None:
        tenant = await self.get_by_alias(alias)
        if not tenant:
            raise KeycloakNotFoundError(f"Tenant not found: {alias}")
        client = await self._client()
        async with client:
            response = await delete_admin_realms_realm_organizations_org_id.asyncio_detailed(
                self._realm,
                tenant.id,
                client=client,
            )
        _check_response(response.status_code, response.content)

    async def update_tenant(self, alias: str, *, name: str, enabled: bool) -> TenantRecord:
        tenant = await self.get_by_alias(alias)
        if not tenant:
            raise KeycloakNotFoundError(f"Tenant not found: {alias}")
        body = OrganizationRepresentation(
            id=tenant.id,
            alias=alias,
            name=name,
            enabled=enabled,
        )
        client = await self._client()
        async with client:
            response = await put_admin_realms_realm_organizations_org_id.asyncio_detailed(
                self._realm,
                tenant.id,
                client=client,
                body=body,
            )
        _check_response(response.status_code, response.content)
        updated = await self.get_by_alias(alias)
        if not updated:
            raise KeycloakAdminError("Tenant updated but could not be resolved")
        return updated

    async def list_members(
        self,
        alias: str,
        *,
        first: int = 0,
        max_results: int = 50,
    ) -> tuple[list[TenantMemberRecord], bool]:
        return await self._members.list_members(alias, first=first, max_results=max_results)

    async def list_tenant_aliases_for_user(self, user_id: str) -> list[str]:
        return await self._members.list_tenant_aliases_for_user(user_id)

    async def _fetch_user_tenant_roles(self, user_id: str) -> dict[str, list[str]]:
        """Load per-tenant roles from the user record (SSOT), not org member attrs."""
        client = await self._client()
        async with client:
            response = await get_admin_realms_realm_users_user_id.asyncio_detailed(
                self._realm,
                user_id,
                client=client,
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, UserRepresentation):
            return {}
        user_attrs = parsed.attributes if parsed.attributes is not UNSET else None
        parsed_attrs = user_attrs if isinstance(user_attrs, UserRepresentationAttributes) else None
        return _parse_tenant_roles(parsed_attrs)
