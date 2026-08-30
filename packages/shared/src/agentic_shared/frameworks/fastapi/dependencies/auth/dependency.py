import logging

from starlette.exceptions import HTTPException

from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.enums import AuthMode
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.settings import AuthSettings

logger = logging.getLogger(__name__)


def require_roles(
    auth: AuthContext,
    settings: AuthSettings,
    *roles: AppRole,
) -> None:
    if settings.auth_mode == AuthMode.NONE:
        return
    if not auth.user_id and settings.auth_mode == AuthMode.JWT:
        logger.warning("unauthorized tenant_id=%s", auth.tenant_id)
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not auth.has_any(*roles):
        logger.warning(
            "forbidden user_id=%s tenant_id=%s",
            auth.user_id,
            auth.tenant_id,
        )
        raise HTTPException(status_code=403, detail="Forbidden")
