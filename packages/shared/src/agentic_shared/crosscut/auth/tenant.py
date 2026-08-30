from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.types import TenantAlias, tenant_alias

DEFAULT_TENANT_ID: TenantAlias = tenant_alias("default")


def resolve_tenant_id(auth: AuthContext) -> TenantAlias:
    if auth.tenant_id:
        return tenant_alias(auth.tenant_id)
    return DEFAULT_TENANT_ID
