from __future__ import annotations

import json
from typing import Self

from pydantic import RootModel, field_validator

from agentic_shared.core.auth.roles import AppRole


class TenantRolesMap(RootModel[dict[str, list[AppRole]]]):
    """Per-tenant role map stored in Keycloak ``tenant_roles`` user attribute / JWT claim."""

    root: dict[str, list[AppRole]]

    @field_validator("root", mode="before")
    @classmethod
    def _coerce_root(cls, value: object) -> dict[str, list[AppRole]]:
        if not isinstance(value, dict):
            return {}
        parsed: dict[str, list[AppRole]] = {}
        for alias, roles in value.items():
            if not isinstance(alias, str) or not isinstance(roles, list):
                continue
            app_roles: list[AppRole] = []
            for role in roles:
                try:
                    app_roles.append(AppRole(str(role)))
                except ValueError:
                    continue
            parsed[alias] = sorted(set(app_roles), key=lambda item: item.value)
        return parsed

    @classmethod
    def parse_raw_value(cls, raw: object) -> Self:
        if raw is None:
            return cls({})
        payload: object = raw
        if isinstance(raw, list) and raw:
            payload = raw[0]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                return cls({})
        if not isinstance(payload, dict):
            return cls({})
        return cls.model_validate(payload)

    def for_tenant(self, alias: str) -> frozenset[AppRole]:
        return frozenset(self.root.get(alias, []))

    def to_role_strings(self) -> dict[str, list[str]]:
        return {alias: [role.value for role in roles] for alias, roles in sorted(self.root.items())}

    def normalize(self) -> TenantRolesMap:
        return TenantRolesMap(
            {
                alias: sorted(set(roles), key=lambda item: item.value)
                for alias, roles in self.root.items()
            }
        )


def serialize_tenant_roles_json(tenant_roles: dict[str, list[str]]) -> list[str]:
    coerced: dict[str, list[AppRole]] = {}
    for alias, roles in tenant_roles.items():
        app_roles: list[AppRole] = []
        for role in roles:
            try:
                app_roles.append(AppRole(role))
            except ValueError:
                continue
        coerced[alias] = app_roles
    payload = TenantRolesMap(coerced).normalize().to_role_strings()
    return [json.dumps(payload, sort_keys=True, separators=(",", ":"))]
