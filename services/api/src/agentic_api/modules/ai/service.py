from agentic_shared.core.compliance.models import AiSystemRecord
from agentic_shared.core.compliance.protocols import AiTransparencyPort

from agentic_api.modules.ai.schemas import AiSystemCardOut


class AiTransparencyService:
    def __init__(self, port: AiTransparencyPort) -> None:
        self._port = port

    def system_card(self) -> AiSystemCardOut:
        return _to_out(self._port.system_record())


def _to_out(record: AiSystemRecord) -> AiSystemCardOut:
    metadata = {str(key): str(value) for key, value in record.metadata.items()}
    return AiSystemCardOut(
        system_name=record.system_name,
        purpose=record.purpose,
        risk_tier=record.risk_tier.value,
        model_id=record.model_id,
        provider=record.provider,
        human_oversight=record.human_oversight,
        logging_enabled=record.logging_enabled,
        metadata=metadata,
    )
