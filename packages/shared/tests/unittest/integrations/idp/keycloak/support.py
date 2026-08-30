from __future__ import annotations

import sys
from http import HTTPStatus
from unittest.mock import MagicMock


def install_keycloak_stubs() -> None:
    if "keycloak_admin_client" in sys.modules:
        return
    root = MagicMock(name="keycloak_admin_client")
    root.AuthenticatedClient = MagicMock
    sys.modules["keycloak_admin_client"] = root

    class _UserRepresentationAttributes:
        def __init__(self) -> None:
            self.additional_properties: dict = {}

        def __setitem__(self, key: str, value: object) -> None:
            self.additional_properties[key] = value

    class _RoleRepresentation:
        def __init__(self, **kwargs: object) -> None:
            self.id = kwargs.get("id", unset)
            self.name = kwargs.get("name", unset)

    class _UnsetType:
        pass

    unset = _UnsetType()

    submodule_names = [
        "api",
        "api.organizations",
        "api.role_mapper",
        "api.roles",
        "api.users",
        "models.credential_representation",
        "models.member_representation",
        "models.member_representation_attributes",
        "models.organization_domain_representation",
        "models.organization_representation",
        "models.role_representation",
        "models.user_representation",
        "models.user_representation_attributes",
        "types",
    ]
    for name in submodule_names:
        full_name = f"keycloak_admin_client.{name}"
        module = MagicMock(name=full_name)
        if name == "types":
            module.UNSET = unset
        if name == "models.user_representation_attributes":
            module.UserRepresentationAttributes = _UserRepresentationAttributes
        if name == "models.role_representation":
            module.RoleRepresentation = _RoleRepresentation
        sys.modules[full_name] = module


class ClientCtx:
    async def __aenter__(self) -> ClientCtx:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None


def org(*, org_id: str = "org-1", alias: str = "acme", name: str = "Acme", enabled: bool = True):
    item = MagicMock()
    item.id = org_id
    item.alias = alias
    item.name = name
    item.enabled = enabled
    return item


def http_response(
    *,
    status: HTTPStatus = HTTPStatus.OK,
    parsed: object = None,
    content: bytes = b"",
    headers: dict | None = None,
):
    response = MagicMock()
    response.status_code = status
    response.parsed = parsed
    response.content = content
    response.headers = headers or {}
    return response
