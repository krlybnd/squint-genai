"""IdP-agnostic admin surface: protocols, records, errors."""

from agentic_shared.integrations.idp.core.errors import (
    IdpConflictError,
    IdpError,
    IdpForbiddenError,
    IdpNotFoundError,
)
from agentic_shared.integrations.idp.core.protocols import (
    TenantAdmin,
    UserAdmin,
    UserTenancyRead,
    UserTenancyWrite,
)
from agentic_shared.integrations.idp.core.records import (
    TenantMemberRecord,
    TenantRecord,
    UserRecord,
    UserTenancy,
)

__all__ = [
    "IdpConflictError",
    "IdpError",
    "IdpForbiddenError",
    "IdpNotFoundError",
    "TenantAdmin",
    "TenantMemberRecord",
    "TenantRecord",
    "UserAdmin",
    "UserRecord",
    "UserTenancy",
    "UserTenancyRead",
    "UserTenancyWrite",
]
