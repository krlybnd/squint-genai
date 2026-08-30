from __future__ import annotations

from typing import TYPE_CHECKING

from keycloak_admin_client.models.user_representation_attributes import UserRepresentationAttributes
from keycloak_admin_client.types import UNSET

from agentic_shared.integrations.idp.keycloak.helpers import (
    _TENANT_ROLES_ATTR,
    _attr_map,
    _serialize_tenant_roles,
)
from agentic_shared.integrations.idp.keycloak.user.models import UserRecord

if TYPE_CHECKING:
    from agentic_shared.integrations.idp.keycloak.user.gateway import UserGateway


class UserAttributes:
    def __init__(self, gateway: UserGateway) -> None:
        self._gateway = gateway

    def _merged_tenant_attributes(
        self,
        existing: UserRepresentationAttributes | None,
        *,
        tenant_id: str | None,
        tenant_roles: dict[str, list[str]],
    ) -> UserRepresentationAttributes:
        attrs = UserRepresentationAttributes()
        for key, values in _attr_map(existing).items():
            if key not in (_TENANT_ROLES_ATTR, "tenant_id"):
                attrs[key] = list(values)
        attrs["tenant_id"] = [tenant_id] if tenant_id else []
        attrs[_TENANT_ROLES_ATTR] = _serialize_tenant_roles(tenant_roles)
        return attrs

    async def put(
        self,
        user: UserRecord,
        *,
        tenant_id: str | None,
        tenant_roles: dict[str, list[str]],
    ) -> None:
        rep = await self._gateway._get_user_representation(user.id)
        existing_attrs = rep.attributes if rep.attributes is not UNSET else None
        parsed_attrs = (
            existing_attrs if isinstance(existing_attrs, UserRepresentationAttributes) else None
        )
        rep.attributes = self._merged_tenant_attributes(
            parsed_attrs,
            tenant_id=tenant_id,
            tenant_roles=tenant_roles,
        )
        await self._gateway._put_user_representation(rep)

    async def set_active_tenant(self, user: UserRecord, tenant_alias: str | None) -> None:
        await self.put(
            user,
            tenant_id=tenant_alias,
            tenant_roles=dict(user.tenant_roles),
        )
