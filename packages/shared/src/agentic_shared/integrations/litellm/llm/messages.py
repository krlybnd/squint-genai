from agentic_shared.domains.chat.roles import LlmMessageRole
from agentic_shared.integrations.litellm.llm.models import ChatMessagePayload


def llm_completion_messages(*items: tuple[LlmMessageRole, str]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for role, content in items:
        payload = ChatMessagePayload(role=role, content=content)
        dumped = payload.model_dump(mode="json", include={"role", "content"})
        messages.append(
            {
                "role": str(dumped["role"]),
                "content": str(dumped.get("content") or ""),
            }
        )
    return messages


def llm_system_user(system: str, user: str) -> list[dict[str, str]]:
    return llm_completion_messages(
        (LlmMessageRole.SYSTEM, system),
        (LlmMessageRole.USER, user),
    )
