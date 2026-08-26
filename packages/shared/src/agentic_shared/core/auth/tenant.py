from agentic_shared.core.auth.context import AuthContext

DEFAULT_TENANT_ID = "default"


def resolve_tenant_id(auth: AuthContext) -> str:
    return auth.tenant_id or DEFAULT_TENANT_ID
