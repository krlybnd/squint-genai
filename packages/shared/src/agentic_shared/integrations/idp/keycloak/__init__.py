"""Keycloak Admin REST integration (Organizations + users)."""

from __future__ import annotations

from keycloak_admin_client.api.organizations import (
    delete_admin_realms_realm_organizations_org_id,
    delete_admin_realms_realm_organizations_org_id_members_member_id,
    get_admin_realms_realm_organizations,
    get_admin_realms_realm_organizations_org_id_members,
    post_admin_realms_realm_organizations,
    post_admin_realms_realm_organizations_org_id_members,
    put_admin_realms_realm_organizations_org_id,
)
from keycloak_admin_client.api.role_mapper import (
    delete_admin_realms_realm_users_user_id_role_mappings_realm,
    get_admin_realms_realm_users_user_id_role_mappings_realm,
    post_admin_realms_realm_users_user_id_role_mappings_realm,
)
from keycloak_admin_client.api.roles import get_admin_realms_realm_roles_role_name
from keycloak_admin_client.api.users import (
    get_admin_realms_realm_users,
    get_admin_realms_realm_users_user_id,
    post_admin_realms_realm_users,
    put_admin_realms_realm_users_user_id,
    put_admin_realms_realm_users_user_id_reset_password,
)
from keycloak_admin_client.models.member_representation import MemberRepresentation

from agentic_shared.integrations.idp.core.records import (
    TenantMemberRecord,
    TenantRecord,
    UserRecord,
)
from agentic_shared.integrations.idp.keycloak.helpers import (
    _check_response,
    _decode_error,
    _location_resource_id,
)
from agentic_shared.integrations.idp.keycloak.tenant.gateway import TenantGateway
from agentic_shared.integrations.idp.keycloak.user.gateway import UserGateway

__all__ = [
    "MemberRepresentation",
    "TenantGateway",
    "TenantMemberRecord",
    "TenantRecord",
    "UserGateway",
    "UserRecord",
    "_check_response",
    "_decode_error",
    "_location_resource_id",
    "delete_admin_realms_realm_organizations_org_id",
    "delete_admin_realms_realm_organizations_org_id_members_member_id",
    "delete_admin_realms_realm_users_user_id_role_mappings_realm",
    "get_admin_realms_realm_organizations",
    "get_admin_realms_realm_organizations_org_id_members",
    "get_admin_realms_realm_roles_role_name",
    "get_admin_realms_realm_users",
    "get_admin_realms_realm_users_user_id",
    "get_admin_realms_realm_users_user_id_role_mappings_realm",
    "post_admin_realms_realm_organizations",
    "post_admin_realms_realm_organizations_org_id_members",
    "post_admin_realms_realm_users",
    "post_admin_realms_realm_users_user_id_role_mappings_realm",
    "put_admin_realms_realm_organizations_org_id",
    "put_admin_realms_realm_users_user_id",
    "put_admin_realms_realm_users_user_id_reset_password",
]
