from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.tenant_roles import TenantRolesMap


class RealmAccessClaims(BaseModel):
    model_config = ConfigDict(extra="ignore")

    roles: list[str] = Field(default_factory=list)


class AccessTokenClaims(BaseModel):
    """OIDC access-token claims used by Squint auth.

    Role source of truth:
    1. ``tenant_roles[tenant_id]`` when present
    2. else flat ``roles`` / ``realm_access.roles`` (legacy tokens)
    """

    model_config = ConfigDict(extra="ignore")

    sub: str | None = None
    preferred_username: str | None = None
    sid: str | None = None
    email: str | None = None
    tenant_id: str | None = None
    roles: list[str] = Field(default_factory=list)
    tenant_roles: list[str] | str | None = None
    realm_access: RealmAccessClaims | None = None

    @field_validator("tenant_id", mode="before")
    @classmethod
    def _coerce_tenant_id(cls, value: object) -> str | None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, str) and first.strip():
                return first.strip()
        return None

    @property
    def user_id(self) -> str:
        for value in (self.sub, self.preferred_username, self.sid, self.email):
            if value:
                return value
        return ""

    def app_roles(self) -> frozenset[AppRole]:
        if self.tenant_id is not None:
            tenant_map = TenantRolesMap.parse_raw_value(self.tenant_roles)
            if self.tenant_id in tenant_map.root:
                return tenant_map.for_tenant(self.tenant_id)
        names = list(self.roles)
        if self.realm_access is not None:
            names.extend(self.realm_access.roles)
        return _roles_from_names(names)


def parse_access_token_claims(claims: dict[str, Any]) -> AccessTokenClaims:
    return AccessTokenClaims.model_validate(claims)


def _roles_from_names(names: list[str]) -> frozenset[AppRole]:
    roles: set[AppRole] = set()
    for name in names:
        try:
            roles.add(AppRole(name))
        except ValueError:
            continue
    return frozenset(roles)
