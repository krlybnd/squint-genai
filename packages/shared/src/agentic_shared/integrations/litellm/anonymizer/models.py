from typing import Any, Self

from pydantic import BaseModel, ConfigDict


class AnonymizeResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str = ""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> Self:
        return cls.model_validate(data)
