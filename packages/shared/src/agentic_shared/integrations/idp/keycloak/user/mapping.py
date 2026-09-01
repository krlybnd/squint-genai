from __future__ import annotations

from typing import TYPE_CHECKING

from keycloak_admin_client.models.user_representation import UserRepresentation
from keycloak_admin_client.models.user_representation_attributes import UserRepresentationAttributes
from keycloak_admin_client.types import UNSET

from agentic_shared.integrations.idp.keycloak.helpers import (
    _attr_map,
    _normalize_roles,
    _parse_tenant_roles,
    _roles_for_tenant,
)
from agentic_shared.integrations.idp.keycloak.user.models import UserRecord

if TYPE_CHECKING:
    from agentic_shared.integrations.idp.keycloak.user.gateway import UserGateway


def tenant_attr(user: UserRepresentation) -> str | None:
    attrs = user.attributes if user.attributes is not UNSET else None
    if not isinstance(attrs, UserRepresentationAttributes):
        return None
    values = _attr_map(attrs).get("tenant_id")
    if values:
        return str(values[0])
    return None


def to_record(user: UserRepresentation) -> UserRecord | None:
    user_id = user.id if user.id is not UNSET and user.id else None
    username = user.username if user.username is not UNSET and user.username else None
    if not user_id or not username:
        return None
    email = user.email if user.email is not UNSET else None
    enabled = bool(user.enabled) if user.enabled is not UNSET else True
    active_tenant = tenant_attr(user)
    user_attrs = user.attributes if user.attributes is not UNSET else None
    parsed_attrs = user_attrs if isinstance(user_attrs, UserRepresentationAttributes) else None
    tenant_roles = _parse_tenant_roles(parsed_attrs)
    if user.realm_roles is not UNSET and user.realm_roles:
        realm_roles = _normalize_roles([str(r) for r in user.realm_roles])
    elif active_tenant:
        realm_roles = _roles_for_tenant(tenant_roles, active_tenant)
    else:
        realm_roles = []
    return UserRecord(
        id=str(user_id),
        username=str(username),
        email=str(email) if email else None,
        enabled=enabled,
        tenant_id=active_tenant,
        tenant_ids=[],
        realm_roles=realm_roles,
        tenant_roles=tenant_roles,
    )


async def with_tenant_memberships(gateway: UserGateway, user: UserRecord) -> UserRecord:
    memberships = await gateway._tenants.list_tenants_for_user(user.id)
    tenant_ids = [item.alias for item in memberships]
    tenant_labels = {item.alias: item.name for item in memberships}
    active = user.tenant_id
    if active and active not in tenant_ids:
        active = tenant_ids[0] if tenant_ids else None
    elif not active and tenant_ids:
        active = tenant_ids[0]
    tenant_roles = {alias: list(user.tenant_roles.get(alias, [])) for alias in tenant_ids}
    realm_roles = _roles_for_tenant(tenant_roles, active) if active else list(user.realm_roles)
    return UserRecord(
        id=user.id,
        username=user.username,
        email=user.email,
        enabled=user.enabled,
        tenant_id=active,
        tenant_ids=tenant_ids,
        realm_roles=realm_roles,
        tenant_roles=tenant_roles,
        tenant_labels=tenant_labels,
    )
