from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from agentic_api.modules.ai.schemas import AiSystemCardOut
from agentic_api.modules.ai.service import AiTransparencyService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/system-card", response_model=AiSystemCardOut)
@inject
async def get_system_card(service: FromDishka[AiTransparencyService]) -> AiSystemCardOut:
    return service.system_card()
