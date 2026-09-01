from __future__ import annotations

from typing import Protocol, runtime_checkable

from agentic_shared.integrations.idp.core.records import (
    TenantMemberRecord,
    TenantRecord,
    UserRecord,
    UserTenancy,
)


@runtime_checkable
class TenantAdmin(Protocol):
    async def list_tenants(self) -> list[TenantRecord]: ...

    async def get_by_alias(self, alias: str) -> TenantRecord | None: ...

    async def create_tenant(self, *, alias: str, name: str) -> TenantRecord: ...

    async def delete_tenant(self, alias: str) -> None: ...

    async def update_tenant(self, alias: str, *, name: str, enabled: bool) -> TenantRecord: ...

    async def list_members(
        self,
        alias: str,
        *,
        first: int = 0,
        max_results: int = 50,
    ) -> tuple[list[TenantMemberRecord], bool]: ...

    async def list_tenants_for_user(self, user_id: str) -> list[TenantRecord]: ...

    async def list_tenant_aliases_for_user(self, user_id: str) -> list[str]: ...


@runtime_checkable
class UserAdmin(Protocol):
    async def list_users(
        self,
        *,
        search: str | None = None,
        first: int = 0,
        max_results: int = 50,
    ) -> tuple[list[UserRecord], bool]: ...

    async def get_by_username(self, username: str) -> UserRecord | None: ...

    async def create_user(
        self,
        *,
        username: str,
        email: str | None,
        password: str,
        realm_roles: list[str] | None = None,
        enabled: bool = True,
    ) -> UserRecord: ...

    async def assign_tenant(
        self,
        username: str,
        tenant_alias: str,
        *,
        set_active: bool | None = None,
        roles: list[str] | None = None,
    ) -> UserRecord: ...

    async def set_tenant_roles(
        self, username: str, tenant_alias: str, roles: list[str]
    ) -> UserRecord: ...

    async def set_active_tenant(self, username: str, tenant_alias: str) -> UserRecord: ...

    async def remove_tenant(self, username: str) -> UserRecord: ...

    async def remove_from_tenant_org(self, username: str, tenant_alias: str) -> UserRecord: ...

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
    ) -> UserRecord: ...


@runtime_checkable
class UserTenancyRead(Protocol):
    async def get(self, username: str) -> UserTenancy | None: ...


@runtime_checkable
class UserTenancyWrite(Protocol):
    async def set_active(self, username: str, tenant_alias: str) -> UserTenancy: ...
