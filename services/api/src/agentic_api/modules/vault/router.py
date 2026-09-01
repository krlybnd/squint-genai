from agentic_shared.crosscut.auth.context import AuthContext
from agentic_shared.crosscut.auth.roles import AppRole
from agentic_shared.crosscut.auth.settings import AuthSettings
from agentic_shared.crosscut.auth.tenant import resolve_tenant_id
from agentic_shared.frameworks.fastapi.dependencies.auth.dependency import require_roles
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from agentic_api.modules.vault.schemas import DetokenizeRequest, DetokenizeResponse
from agentic_api.modules.vault.service import VaultApiService

router = APIRouter(prefix="/vault", tags=["vault"])


@router.post("/detokenize", response_model=DetokenizeResponse)
@inject
async def detokenize(
    body: DetokenizeRequest,
    auth: FromDishka[AuthContext],
    auth_settings: FromDishka[AuthSettings],
    service: FromDishka[VaultApiService],
) -> DetokenizeResponse:
    require_roles(auth, auth_settings, AppRole.READ)
    tenant_id = resolve_tenant_id(auth)
    return await service.detokenize(body.tokens, auth=auth, tenant_id=tenant_id)


__all__ = ["router"]
