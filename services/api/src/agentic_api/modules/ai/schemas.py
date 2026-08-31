from pydantic import BaseModel, Field


class AiSystemCardOut(BaseModel):
    system_name: str
    purpose: str
    risk_tier: str
    model_id: str
    provider: str
    human_oversight: bool
    logging_enabled: bool
    metadata: dict[str, str] = Field(default_factory=dict)
