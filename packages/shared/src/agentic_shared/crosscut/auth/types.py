"""Shared auth primitive types (tenant alias, role sets)."""

from __future__ import annotations

from typing import NewType

from agentic_shared.crosscut.auth.roles import AppRole

TenantAlias = NewType("TenantAlias", str)

type TenantRoleSet = frozenset[AppRole]
type TenantRolesByAlias = dict[TenantAlias, TenantRoleSet]


def tenant_alias(value: str) -> TenantAlias:
    """Normalize a non-empty tenant alias string."""
    stripped = value.strip()
    if not stripped:
        raise ValueError("tenant alias must be non-empty")
    return TenantAlias(stripped)
