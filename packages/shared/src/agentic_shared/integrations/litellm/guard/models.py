from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field


class GuardResult(BaseModel):
    """Guard ``/analyze/prompt`` (or ``/scan/prompt``) response."""

    model_config = ConfigDict(extra="allow")

    is_valid: bool = True
    scanners: dict[str, float] = Field(default_factory=dict)
    sanitized_prompt: str | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> Self:
        return cls.model_validate(data)

    @property
    def is_injection(self) -> bool:
        return not self.is_valid
