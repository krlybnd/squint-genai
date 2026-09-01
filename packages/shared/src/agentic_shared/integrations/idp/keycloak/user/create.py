from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from keycloak_admin_client.api.users import post_admin_realms_realm_users
from keycloak_admin_client.models.credential_representation import CredentialRepresentation
from keycloak_admin_client.models.user_representation import UserRepresentation
from keycloak_admin_client.types import UNSET

from agentic_shared.integrations.idp.keycloak.errors import (
    KeycloakAdminError,
    KeycloakConflictError,
)
from agentic_shared.integrations.idp.keycloak.helpers import _check_response, _location_resource_id
from agentic_shared.integrations.idp.keycloak.user.models import UserRecord

if TYPE_CHECKING:
    from agentic_shared.integrations.idp.keycloak.user.gateway import UserGateway


async def create_user(
    gateway: UserGateway,
    *,
    username: str,
    email: str | None,
    password: str,
    realm_roles: list[str] | None = None,
    enabled: bool = True,
) -> UserRecord:
    if await gateway.get_by_username(username):
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
    client = await gateway._client()
    async with client:
        response = await post_admin_realms_realm_users.asyncio_detailed(
            gateway._realm,
            client=client,
            body=body,
        )
    if response.status_code == HTTPStatus.CONFLICT:
        raise KeycloakConflictError(f"User already exists: {username}")
    _check_response(response.status_code, response.content)

    user_id = _location_resource_id(dict(response.headers))
    user = await gateway.get_by_username(username)
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
            tenant_roles=dict(user.tenant_roles),
            tenant_labels=dict(user.tenant_labels),
        )

    if realm_roles:
        await gateway._realm_roles.sync(user.id, realm_roles)
        refreshed = await gateway.get_by_username(username)
        if refreshed:
            user = refreshed
    return user
