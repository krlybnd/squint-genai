from agentic_shared.core.compliance.protocols import AiTransparencyPort
from dishka import Provider, Scope, provide

from agentic_api.modules.ai.service import AiTransparencyService


class AiProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def ai_transparency_service(self, port: AiTransparencyPort) -> AiTransparencyService:
        return AiTransparencyService(port)
