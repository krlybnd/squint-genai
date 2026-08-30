from __future__ import annotations

import json
from http import HTTPStatus
from urllib.parse import urlparse

from keycloak_admin_client.models.member_representation_attributes import (
    MemberRepresentationAttributes,
)
from keycloak_admin_client.models.user_representation_attributes import UserRepresentationAttributes

from agentic_shared.crosscut.auth.claims import TenantRolesMap, serialize_tenant_roles_json
from agentic_shared.integrations.idp.keycloak.errors import (
    KeycloakAdminError,
    KeycloakConflictError,
    KeycloakForbiddenError,
    KeycloakNotFoundError,
)

_APP_REALM_ROLES = frozenset({"read", "write", "admin"})
_TENANT_ROLES_ATTR = "tenant_roles"


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


def _normalize_roles(roles: list[str] | None) -> list[str]:
    if not roles:
        return []
    return sorted({role for role in roles if role in _APP_REALM_ROLES})


def _attr_map(
    attributes: UserRepresentationAttributes | MemberRepresentationAttributes | None,
) -> dict[str, list[str]]:
    if attributes is None:
        return {}
    out: dict[str, list[str]] = {}
    for key, value in attributes.additional_properties.items():
        if isinstance(value, list):
            out[str(key)] = [str(item) for item in value]
    return out


def _parse_tenant_roles(
    attributes: UserRepresentationAttributes | MemberRepresentationAttributes | None,
) -> dict[str, list[str]]:
    """Wire form for IdP records (sorted role name lists)."""
    values = _attr_map(attributes).get(_TENANT_ROLES_ATTR)
    if not values:
        return {}
    return TenantRolesMap.parse_raw_value(values).to_role_strings()


def _serialize_tenant_roles(tenant_roles: dict[str, list[str]]) -> list[str]:
    return serialize_tenant_roles_json(tenant_roles)


def _roles_for_tenant(tenant_roles: dict[str, list[str]], alias: str) -> list[str]:
    return list(tenant_roles.get(alias, []))
