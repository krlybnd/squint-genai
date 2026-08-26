from typing import Any, Self

from pydantic import BaseModel, ConfigDict

from agentic_shared.domains.chat.roles import LlmMessageRole


class ChatMessagePayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    role: LlmMessageRole = LlmMessageRole.USER
    content: str | None = None


class ChatCompletionChoice(BaseModel):
    model_config = ConfigDict(extra="allow")

    message: ChatMessagePayload = ChatMessagePayload()


class ChatCompletionResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    choices: list[ChatCompletionChoice] = []

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> Self:
        return cls.model_validate(data)

    @property
    def content(self) -> str:
        if not self.choices:
            return ""
        return str(self.choices[0].message.content or "")
