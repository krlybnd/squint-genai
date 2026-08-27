import logging

from agentic_shared.core.i18n import DEFAULT_LOCALE, LOCALE_LANGUAGE, SUPPORTED_LOCALES, t
from agentic_shared.integrations.llm.content import extract_chat_completion_content
from agentic_shared.integrations.llm.messages import llm_system_user
from agentic_shared.integrations.llm.protocols import ChatClient
from agentic_shared.integrations.llm.settings import LLMSettings

from agentic_chat.modules.chat.settings import get_module_settings

logger = logging.getLogger(__name__)

# Canonical DB / API default (matches session.default_title in en.json).
DEFAULT_SESSION_TITLE = "New chat"


def default_session_title(locale: str = DEFAULT_LOCALE) -> str:
    return t("session.default_title", locale)


class SessionTitleGenerator:
    def __init__(self, chat_client: ChatClient) -> None:
        self._chat = chat_client

    @staticmethod
    def is_default_title(title: str | None) -> bool:
        if not title or not title.strip():
            return True
        stripped = title.strip()
        if stripped == DEFAULT_SESSION_TITLE:
            return True
        return any(stripped == t("session.default_title", loc) for loc in SUPPORTED_LOCALES)

    async def generate(self, user_message: str, *, locale: str = DEFAULT_LOCALE) -> str:
        module = get_module_settings()
        language = LOCALE_LANGUAGE.get(locale, locale)
        system = t("session.title_system_prompt", locale, language=language)
        result = await self._chat.chat_completion(
            messages=llm_system_user(system, user_message[: module.user_message_preview_chars]),
            temperature=module.session_title_temperature,
            model=LLMSettings().litellm_router_model,
        )
        raw = extract_chat_completion_content(result)
        title = raw.strip().strip("\"'«»„“”")
        if not title:
            title = user_message.strip()[:60] or default_session_title(locale)
        title = title[: module.session_title_max_chars]
        logger.debug("generated session title chars=%d", len(title))
        return title
