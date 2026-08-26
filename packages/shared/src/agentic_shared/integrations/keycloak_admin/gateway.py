from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from urllib.parse import urlparse

from keycloak_admin_client import AuthenticatedClient
from keycloak_admin_client.api.organizations import (
    delete_admin_realms_realm_organizations_org_id,
    delete_admin_realms_realm_organizations_org_id_members_member_id,
    get_admin_realms_realm_organizations,
    get_admin_realms_realm_organizations_org_id_members,
    post_admin_realms_realm_organizations,
    post_admin_realms_realm_organizations_org_id_members,
    put_admin_realms_realm_organizations_org_id,
)
from keycloak_admin_client.api.role_mapper import (
    delete_admin_realms_realm_users_user_id_role_mappings_realm,
    post_admin_realms_realm_users_user_id_role_mappings_realm,
)
from keycloak_admin_client.api.users import (
    get_admin_realms_realm_users,
    post_admin_realms_realm_users,
    put_admin_realms_realm_users_user_id,
    put_admin_realms_realm_users_user_id_reset_password,
)
from keycloak_admin_client.models.credential_representation import CredentialRepresentation
from keycloak_admin_client.models.member_representation import MemberRepresentation
from keycloak_admin_client.models.organization_domain_representation import (
    OrganizationDomainRepresentation,
)
from keycloak_admin_client.models.organization_representation import OrganizationRepresentation
from keycloak_admin_client.models.role_representation import RoleRepresentation
from keycloak_admin_client.models.user_representation import UserRepresentation
from keycloak_admin_client.models.user_representation_attributes import UserRepresentationAttributes
from keycloak_admin_client.types import UNSET

from agentic_shared.integrations.keycloak_admin.client import KeycloakAdminClientFactory
from agentic_shared.integrations.keycloak_admin.errors import (
    KeycloakAdminError,
    KeycloakConflictError,
    KeycloakForbiddenError,
    KeycloakNotFoundError,
)
from agentic_shared.integrations.keycloak_admin.settings import KeycloakAdminSettings


@dataclass(frozen=True, slots=True)
class TenantMemberRecord:
    id: str
    username: str
    email: str | None


@dataclass(frozen=True, slots=True)
class TenantRecord:
    id: str
    alias: str
    name: str
    enabled: bool


@dataclass(frozen=True, slots=True)
class UserRecord:
    id: str
    username: str
    email: str | None
    enabled: bool
    tenant_id: str | None
    tenant_ids: list[str]
    realm_roles: list[str]


def _location_resource_id(headers: dict[str, str]) -> str | None:
    location = headers.get("Location") or headers.get("location")
    if not location:
        return None
    path = urlparse(location).path.rstrip("/")
    if not path:
        return None
    return path.split("/")[-1] or None


def _decode_error(content: bytes) -> str:
    if not content:
        return "Keycloak request failed"
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return str(data.get("errorMessage") or data.get("error") or content.decode())
    except json.JSONDecodeError:
        pass
    return content.decode(errors="replace")


def _check_response(status: HTTPStatus, content: bytes) -> None:
    if status in (HTTPStatus.CREATED, HTTPStatus.NO_CONTENT, HTTPStatus.OK):
        return
    message = _decode_error(content)
    if status == HTTPStatus.NOT_FOUND:
        raise KeycloakNotFoundError(message)
    if status == HTTPStatus.CONFLICT:
        raise KeycloakConflictError(message)
    if status == HTTPStatus.FORBIDDEN:
        raise KeycloakForbiddenError(message)
    raise KeycloakAdminError(f"{status.value}: {message}")


class TenantGateway:
    def __init__(
        self, settings: KeycloakAdminSettings, factory: KeycloakAdminClientFactory
    ) -> None:
        self._settings = settings
        self._factory = factory

    @property
    def _realm(self) -> str:
        return self._settings.keycloak_realm

    async def _client(self) -> AuthenticatedClient:
        return await self._factory.authenticated_client()

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
        # Keycloak org search (exact) often returns empty; resolve from the org list.
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
        tenant = await self.get_by_alias(alias)
        if not tenant:
            raise KeycloakNotFoundError(f"Tenant not found: {alias}")
        page_size = max(1, min(max_results, 200))
        client = await self._client()
        async with client:
            response = await get_admin_realms_realm_organizations_org_id_members.asyncio_detailed(
                self._realm,
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
        for item in parsed:
            if not isinstance(item, MemberRepresentation):
                continue
            user_id = item.id if item.id is not UNSET and item.id else None
            username = item.username if item.username is not UNSET and item.username else None
            if not user_id or not username or str(username).startswith("service-account-"):
                continue
            email = item.email if item.email is not UNSET and item.email else None
            members.append(
                TenantMemberRecord(
                    id=str(user_id),
                    username=str(username),
                    email=str(email) if email else None,
                )
            )
        has_more = len(parsed) >= page_size
        return members, has_more

    async def list_tenant_aliases_for_user(self, user_id: str) -> list[str]:
        aliases: list[str] = []
        for tenant in await self.list_tenants():
            members, _ = await self.list_members(tenant.alias, first=0, max_results=500)
            if any(m.id == user_id for m in members):
                aliases.append(tenant.alias)
        return sorted(aliases)


class UserGateway:
    def __init__(
        self, settings: KeycloakAdminSettings, factory: KeycloakAdminClientFactory
    ) -> None:
        self._settings = settings
        self._factory = factory
        self._tenants = TenantGateway(settings, factory)

    @property
    def _realm(self) -> str:
        return self._settings.keycloak_realm

    async def _client(self) -> AuthenticatedClient:
        return await self._factory.authenticated_client()

    def _tenant_attr(self, user: UserRepresentation) -> str | None:
        attrs = user.attributes
        if attrs is UNSET or not isinstance(attrs, UserRepresentationAttributes):
            return None
        values = attrs.additional_properties.get("tenant_id")
        if isinstance(values, list) and values:
            return str(values[0])
        return None

    def _roles(self, user: UserRepresentation) -> list[str]:
        if user.realm_roles is UNSET or not user.realm_roles:
            return []
        return [str(r) for r in user.realm_roles]

    def _to_record(self, user: UserRepresentation) -> UserRecord | None:
        user_id = user.id if user.id is not UNSET and user.id else None
        username = user.username if user.username is not UNSET and user.username else None
        if not user_id or not username:
            return None
        email = user.email if user.email is not UNSET else None
        enabled = bool(user.enabled) if user.enabled is not UNSET else True
        return UserRecord(
            id=str(user_id),
            username=str(username),
            email=str(email) if email else None,
            enabled=enabled,
            tenant_id=self._tenant_attr(user),
            tenant_ids=[],
            realm_roles=self._roles(user),
        )

    async def _with_tenant_memberships(self, user: UserRecord) -> UserRecord:
        tenant_ids = await self._tenants.list_tenant_aliases_for_user(user.id)
        active = user.tenant_id
        if active and active not in tenant_ids:
            active = tenant_ids[0] if tenant_ids else None
        elif not active and tenant_ids:
            active = tenant_ids[0]
        return UserRecord(
            id=user.id,
            username=user.username,
            email=user.email,
            enabled=user.enabled,
            tenant_id=active,
            tenant_ids=tenant_ids,
            realm_roles=user.realm_roles,
        )

    async def list_users(
        self,
        *,
        search: str | None = None,
        first: int = 0,
        max_results: int = 50,
    ) -> tuple[list[UserRecord], bool]:
        page_size = max(1, min(max_results, 200))
        client = await self._client()
        async with client:
            response = await get_admin_realms_realm_users.asyncio_detailed(
                self._realm,
                client=client,
                search=search if search else UNSET,
                first=max(0, first),
                max_=page_size,
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, list):
            return [], False
        records: list[UserRecord] = []
        for item in parsed:
            record = self._to_record(item)
            if record:
                records.append(await self._with_tenant_memberships(record))
        has_more = len(parsed) >= page_size
        return records, has_more

    async def get_by_username(self, username: str) -> UserRecord | None:
        client = await self._client()
        async with client:
            response = await get_admin_realms_realm_users.asyncio_detailed(
                self._realm,
                client=client,
                username=username,
                exact=True,
                max_=5,
            )
        _check_response(response.status_code, response.content)
        parsed = response.parsed
        if not isinstance(parsed, list) or not parsed:
            return None
        record = self._to_record(parsed[0])
        if not record:
            return None
        return await self._with_tenant_memberships(record)

    async def create_user(
        self,
        *,
        username: str,
        email: str | None,
        password: str,
        realm_roles: list[str] | None = None,
        enabled: bool = True,
    ) -> UserRecord:
        if await self.get_by_username(username):
            raise KeycloakConflictError(f"User already exists: {username}")

        credentials = [
            CredentialRepresentation(type_="password", value=password, temporary=False),
        ]
        body = UserRepresentation(
            username=username,
            email=email or UNSET,
            enabled=enabled,
            email_verified=True if email else UNSET,
            credentials=credentials,
        )
        client = await self._client()
        async with client:
            response = await post_admin_realms_realm_users.asyncio_detailed(
                self._realm,
                client=client,
                body=body,
            )
        if response.status_code == HTTPStatus.CONFLICT:
            raise KeycloakConflictError(f"User already exists: {username}")
        _check_response(response.status_code, response.content)

        user_id = _location_resource_id(dict(response.headers))
        user = await self.get_by_username(username)
        if not user:
            raise KeycloakAdminError("User created but could not be resolved")
        if user_id and user.id != user_id:
            user = UserRecord(
                id=user_id,
                username=user.username,
                email=user.email,
                enabled=user.enabled,
                tenant_id=user.tenant_id,
                tenant_ids=user.tenant_ids,
                realm_roles=user.realm_roles,
            )

        if realm_roles:
            await self._assign_realm_roles(user.id, realm_roles)
            refreshed = await self.get_by_username(username)
            if refreshed:
                user = refreshed
        return user

    async def _assign_realm_roles(self, user_id: str, roles: list[str]) -> None:
        if not roles:
            return
        body = [RoleRepresentation(name=role) for role in roles]
        client = await self._client()
        async with client:
            response = (
                await post_admin_realms_realm_users_user_id_role_mappings_realm.asyncio_detailed(
                    self._realm,
                    user_id,
                    client=client,
                    body=body,
                )
            )
        _check_response(response.status_code, response.content)

    async def _set_tenant_attribute(self, user: UserRecord, tenant_alias: str | None) -> None:
        attrs = UserRepresentationAttributes()
        if tenant_alias:
            attrs["tenant_id"] = [tenant_alias]
        else:
            attrs["tenant_id"] = []

        body = UserRepresentation(
            id=user.id,
            username=user.username,
            attributes=attrs,
        )
        client = await self._client()
        async with client:
            response = await put_admin_realms_realm_users_user_id.asyncio_detailed(
                self._realm,
                user.id,
                client=client,
                body=body,
            )
        _check_response(response.status_code, response.content)

    async def assign_tenant(
        self,
        username: str,
        tenant_alias: str,
        *,
        set_active: bool | None = None,
    ) -> UserRecord:
        user = await self.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")
        tenant = await self._tenants.get_by_alias(tenant_alias)
        if not tenant:
            raise KeycloakNotFoundError(f"Tenant not found: {tenant_alias}")

        client = await self._client()
        async with client:
            response = await post_admin_realms_realm_organizations_org_id_members.asyncio_detailed(
                self._realm,
                tenant.id,
                client=client,
                body=user.id,
            )
        if response.status_code not in (HTTPStatus.CREATED, HTTPStatus.CONFLICT):
            _check_response(response.status_code, response.content)

        should_set_active = set_active if set_active is not None else user.tenant_id is None
        if should_set_active:
            await self._set_tenant_attribute(user, tenant_alias)

        refreshed = await self.get_by_username(username)
        if not refreshed:
            raise KeycloakAdminError("User tenant assignment failed")
        return refreshed

    async def set_active_tenant(self, username: str, tenant_alias: str) -> UserRecord:
        user = await self.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")
        if tenant_alias not in user.tenant_ids:
            raise KeycloakNotFoundError(f"User is not a member of tenant: {tenant_alias}")
        await self._set_tenant_attribute(user, tenant_alias)
        refreshed = await self.get_by_username(username)
        if not refreshed:
            raise KeycloakAdminError("Active tenant update failed")
        return refreshed

    async def remove_tenant(self, username: str) -> UserRecord:
        """Remove active tenant membership and clear active tenant attribute."""
        user = await self.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")
        if not user.tenant_id:
            return user
        return await self.remove_from_tenant_org(username, user.tenant_id)

    async def remove_from_tenant_org(self, username: str, tenant_alias: str) -> UserRecord:
        user = await self.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")
        tenant = await self._tenants.get_by_alias(tenant_alias)
        if not tenant:
            raise KeycloakNotFoundError(f"Tenant not found: {tenant_alias}")

        client = await self._client()
        async with client:
            remove_member = (
                delete_admin_realms_realm_organizations_org_id_members_member_id.asyncio_detailed
            )
            response = await remove_member(
                self._realm,
                tenant.id,
                user.id,
                client=client,
            )
        if response.status_code not in (HTTPStatus.NO_CONTENT, HTTPStatus.NOT_FOUND):
            _check_response(response.status_code, response.content)

        remaining = [a for a in user.tenant_ids if a != tenant_alias]
        if user.tenant_id == tenant_alias:
            new_active = remaining[0] if remaining else None
            await self._set_tenant_attribute(user, new_active)

        refreshed = await self.get_by_username(username)
        if not refreshed:
            raise KeycloakAdminError("User tenant removal failed")
        return refreshed

    _APP_REALM_ROLES = frozenset({"read", "write", "admin"})

    async def _sync_realm_roles(self, user: UserRecord, desired_roles: list[str]) -> None:
        desired = {r for r in desired_roles if r in self._APP_REALM_ROLES}
        current = {r for r in user.realm_roles if r in self._APP_REALM_ROLES}
        to_remove = current - desired
        to_add = desired - current
        client = await self._client()
        async with client:
            if to_remove:
                body = [RoleRepresentation(name=role) for role in sorted(to_remove)]
                delete_roles = (
                    delete_admin_realms_realm_users_user_id_role_mappings_realm.asyncio_detailed
                )
                response = await delete_roles(
                    self._realm,
                    user.id,
                    client=client,
                    body=body,
                )
                _check_response(response.status_code, response.content)
            if to_add:
                body = [RoleRepresentation(name=role) for role in sorted(to_add)]
                add_roles = (
                    post_admin_realms_realm_users_user_id_role_mappings_realm.asyncio_detailed
                )
                response = await add_roles(
                    self._realm,
                    user.id,
                    client=client,
                    body=body,
                )
                _check_response(response.status_code, response.content)

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
        user = await self.get_by_username(username)
        if not user:
            raise KeycloakNotFoundError(f"User not found: {username}")

        body = UserRepresentation(
            id=user.id,
            username=user.username,
            email=email if email is not None else (user.email or UNSET),
            enabled=enabled if enabled is not None else user.enabled,
        )
        client = await self._client()
        async with client:
            response = await put_admin_realms_realm_users_user_id.asyncio_detailed(
                self._realm,
                user.id,
                client=client,
                body=body,
            )
            _check_response(response.status_code, response.content)
            if password:
                cred = CredentialRepresentation(type_="password", value=password, temporary=False)
                pw_response = (
                    await put_admin_realms_realm_users_user_id_reset_password.asyncio_detailed(
                        self._realm,
                        user.id,
                        client=client,
                        body=cred,
                    )
                )
                _check_response(pw_response.status_code, pw_response.content)

        if realm_roles is not None:
            refreshed = await self.get_by_username(username)
            if not refreshed:
                raise KeycloakAdminError("User update failed")
            await self._sync_realm_roles(refreshed, realm_roles)

        if clear_tenant:
            await self.remove_tenant(username)
        elif tenant_alias is not None and tenant_alias.strip():
            alias = tenant_alias.strip()
            refreshed = await self.get_by_username(username)
            if refreshed and refreshed.tenant_id != alias:
                await self.assign_tenant(username, alias, set_active=True)

        final = await self.get_by_username(username)
        if not final:
            raise KeycloakAdminError("User update failed")
        return final
