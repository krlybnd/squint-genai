"""Typed OIDC access-token claims and per-tenant role maps."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator

from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.types import (
    TenantAlias,
    TenantRolesByAlias,
    TenantRoleSet,
    tenant_alias,
)


def _coerce_role_set(roles: object) -> TenantRoleSet:
    if not isinstance(roles, (list, tuple, set, frozenset)):
        return frozenset()
    parsed: set[AppRole] = set()
    for role in roles:
        try:
            parsed.add(AppRole(str(role)))
        except ValueError:
            continue
    return frozenset(parsed)


class TenantRolesMap(RootModel[TenantRolesByAlias]):
    """Per-tenant role map from Keycloak ``tenant_roles`` attribute / JWT claim."""

    root: TenantRolesByAlias

    @field_validator("root", mode="before")
    @classmethod
    def _coerce_root(cls, value: object) -> TenantRolesByAlias:
        if not isinstance(value, dict):
            return {}
        parsed: TenantRolesByAlias = {}
        for alias, roles in value.items():
            if not isinstance(alias, str):
                continue
            try:
                key = tenant_alias(alias)
            except ValueError:
                continue
            parsed[key] = _coerce_role_set(roles)
        return parsed

    @classmethod
    def parse_raw_value(cls, raw: object) -> Self:
        """Accept JWT multivalued claim or admin-attribute list / JSON string / dict."""
        if raw is None:
            return cls({})
        payload: object = raw[0] if isinstance(raw, list) and raw else raw
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return cls({})
        if not isinstance(payload, dict):
            return cls({})
        return cls.model_validate(payload)

    def for_tenant(self, alias: TenantAlias | str) -> TenantRoleSet:
        try:
            key = tenant_alias(str(alias))
        except ValueError:
            return frozenset()
        return self.root.get(key, frozenset())

    def to_role_strings(self) -> dict[str, list[str]]:
        """Wire form for Keycloak attributes / JSON claims (sorted role names)."""
        return {
            str(alias): sorted(role.value for role in roles)
            for alias, roles in sorted(self.root.items(), key=lambda item: str(item[0]))
        }


def serialize_tenant_roles_json(
    tenant_roles: TenantRolesMap | Mapping[str, Sequence[str]],
) -> list[str]:
    mapping = (
        tenant_roles
        if isinstance(tenant_roles, TenantRolesMap)
        else TenantRolesMap.parse_raw_value(dict(tenant_roles))
    )
    return [json.dumps(mapping.to_role_strings(), sort_keys=True, separators=(",", ":"))]


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
    tenant_id: TenantAlias | None = None
    roles: list[str] = Field(default_factory=list)
    tenant_roles: list[str] | str | None = None
    realm_access: RealmAccessClaims | None = None

    @field_validator("tenant_id", mode="before")
    @classmethod
    def _coerce_tenant_id(cls, value: object) -> TenantAlias | None:
        if isinstance(value, str) and value.strip():
            return tenant_alias(value)
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, str) and first.strip():
                return tenant_alias(first)
        return None

    @property
    def user_id(self) -> str:
        for value in (self.sub, self.preferred_username, self.sid, self.email):
            if value:
                return value
        return ""

    def app_roles(self) -> TenantRoleSet:
        if self.tenant_id is not None:
            tenant_map = TenantRolesMap.parse_raw_value(self.tenant_roles)
            if self.tenant_id in tenant_map.root:
                return tenant_map.for_tenant(self.tenant_id)
        names = list(self.roles)
        if self.realm_access is not None:
            names.extend(self.realm_access.roles)
        return _roles_from_names(names)


def parse_access_token_claims(claims: Mapping[str, Any]) -> AccessTokenClaims:
    return AccessTokenClaims.model_validate(dict(claims))


def _roles_from_names(names: Sequence[str]) -> TenantRoleSet:
    roles: set[AppRole] = set()
    for name in names:
        try:
            roles.add(AppRole(name))
        except ValueError:
            continue
    return frozenset(roles)
