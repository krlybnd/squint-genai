from typing import Any

from agentic_shared.integrations.llm.models import ChatCompletionResult


def extract_chat_completion_content(result: ChatCompletionResult | dict[str, Any] | Any) -> str:
    if isinstance(result, ChatCompletionResult):
        return result.content
    if isinstance(result, dict):
        return ChatCompletionResult.from_api_response(result).content
    return ""
