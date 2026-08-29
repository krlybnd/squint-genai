from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agentic_shared.core.auth.roles import AppRole
from agentic_shared.core.auth.tenant_roles import TenantRolesMap


class RealmAccessClaims(BaseModel):
    model_config = ConfigDict(extra="ignore")

    roles: list[str] = Field(default_factory=list)


class AccessTokenClaims(BaseModel):
    """Validated OIDC access-token claims used by Squint auth."""

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
    def active_tenant_id(self) -> str | None:
        return self.tenant_id

    def tenant_roles_map(self) -> TenantRolesMap:
        return TenantRolesMap.parse_raw_value(self.tenant_roles)

    def flat_app_roles(self) -> frozenset[AppRole]:
        names: set[str] = set(self.roles)
        if self.realm_access is not None:
            names.update(self.realm_access.roles)
        roles: set[AppRole] = set()
        for name in names:
            try:
                roles.add(AppRole(name))
            except ValueError:
                continue
        return frozenset(roles)

    def effective_app_roles(self) -> frozenset[AppRole]:
        tenant_id = self.active_tenant_id
        tenant_roles = self.tenant_roles_map()
        if tenant_id is not None and tenant_id in tenant_roles.root:
            return tenant_roles.for_tenant(tenant_id)
        return self.flat_app_roles()


def parse_access_token_claims(claims: dict[str, Any]) -> AccessTokenClaims:
    return AccessTokenClaims.model_validate(claims)


def parse_tenant_id_from_claims(claims: dict[str, Any]) -> str | None:
    return parse_access_token_claims(claims).active_tenant_id


def parse_tenant_roles_claim(raw: object) -> dict[str, list[str]]:
    return TenantRolesMap.parse_raw_value(raw).to_role_strings()


def extract_flat_keycloak_roles(claims: dict[str, Any]) -> set[str]:
    return {role.value for role in parse_access_token_claims(claims).flat_app_roles()}


def extract_keycloak_roles(claims: dict[str, Any]) -> set[str]:
    return {role.value for role in parse_access_token_claims(claims).effective_app_roles()}
