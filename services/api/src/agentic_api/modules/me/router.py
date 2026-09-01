from agentic_shared.core.compliance.enums import AuditEventCategory
from agentic_shared.core.compliance.models import AuditEvent
from agentic_shared.core.compliance.protocols import AuditLogger
from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.settings import AuthSettings
from agentic_shared.domains.persistence.audit_logger import emit_audit
from agentic_shared.frameworks.fastapi.dependencies.auth.dependency import require_roles
from agentic_shared.integrations.idp.core.errors import (
    IdpError,
    IdpForbiddenError,
    IdpNotFoundError,
)
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, HTTPException

from agentic_api.modules.me.schemas import MeOut, SetMyActiveTenantRequest
from agentic_api.modules.me.service import MeService

router = APIRouter(prefix="/me", tags=["me"])


def _caller_username(auth: AuthContext) -> str:
    username = auth.username or auth.user_id
    if not username:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return username


@router.get("", response_model=MeOut)
@inject
async def get_me(
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[MeService],
) -> MeOut:
    require_roles(auth, auth_settings, AppRole.READ, AppRole.WRITE, AppRole.ADMIN)
    try:
        return await service.get_me(_caller_username(auth))
    except IdpNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.put("/active-tenant", response_model=MeOut)
@inject
async def set_my_active_tenant(
    body: SetMyActiveTenantRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[MeService],
    audit: FromDishka[AuditLogger],
) -> MeOut:
    require_roles(auth, auth_settings, AppRole.READ, AppRole.WRITE, AppRole.ADMIN)
    try:
        out = await service.set_active_tenant(_caller_username(auth), body.alias)
    except IdpForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except IdpNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except IdpError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    await emit_audit(
        audit,
        AuditEvent(
            category=AuditEventCategory.ACCESS,
            action="tenant.switch",
            actor_id=auth.user_id,
            tenant_id=out.tenant_id,
            resource_type="tenant",
            resource_id=body.alias,
        ),
    )
    return out
