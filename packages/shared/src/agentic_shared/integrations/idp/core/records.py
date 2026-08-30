from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TenantMemberRecord:
    id: str
    username: str
    email: str | None
    roles: list[str]


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
    tenant_roles: dict[str, list[str]]
