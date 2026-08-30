from __future__ import annotations

from typing import TYPE_CHECKING

from keycloak_admin_client.api.users import put_admin_realms_realm_users_user_id_reset_password
from keycloak_admin_client.models.credential_representation import CredentialRepresentation
from keycloak_admin_client.types import UNSET

from agentic_shared.integrations.idp.keycloak.errors import (
    KeycloakAdminError,
    KeycloakNotFoundError,
)
from agentic_shared.integrations.idp.keycloak.helpers import _check_response
from agentic_shared.integrations.idp.keycloak.user.models import UserRecord

if TYPE_CHECKING:
    from agentic_shared.integrations.idp.keycloak.user.gateway import UserGateway


async def update_user(
    gateway: UserGateway,
    username: str,
    *,
    email: str | None = None,
    enabled: bool | None = None,
    realm_roles: list[str] | None = None,
    tenant_alias: str | None = None,
    clear_tenant: bool = False,
    password: str | None = None,
) -> UserRecord:
    user = await gateway.get_by_username(username)
    if not user:
        raise KeycloakNotFoundError(f"User not found: {username}")

    rep = await gateway._repo.get_representation(user.id)
    if email is not None:
        rep.email = email if email else UNSET
    if enabled is not None:
        rep.enabled = enabled
    await gateway._repo.put_representation(rep)

    client = await gateway._client()
    async with client:
        if password:
            cred = CredentialRepresentation(type_="password", value=password, temporary=False)
            pw_response = (
                await put_admin_realms_realm_users_user_id_reset_password.asyncio_detailed(
                    gateway._realm,
                    user.id,
                    client=client,
                    body=cred,
                )
            )
            _check_response(pw_response.status_code, pw_response.content)

    if realm_roles is not None:
        if user.tenant_id:
            await gateway.set_tenant_roles(username, user.tenant_id, realm_roles)
        else:
            await gateway._realm_roles.sync(user.id, realm_roles)

    if clear_tenant:
        await gateway.remove_tenant(username)
    elif tenant_alias is not None and tenant_alias.strip():
        alias = tenant_alias.strip()
        refreshed = await gateway.get_by_username(username)
        if refreshed and refreshed.tenant_id != alias:
            await gateway.assign_tenant(username, alias, set_active=True)

    final = await gateway.get_by_username(username)
    if not final:
        raise KeycloakAdminError("User update failed")
    return final
