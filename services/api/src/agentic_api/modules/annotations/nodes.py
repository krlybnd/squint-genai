import json
import logging
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from agentic_shared.core.security.guard import looks_like_prompt_injection
from agentic_shared.crosscut.i18n import DEFAULT_LOCALE, LOCALE_LANGUAGE, t
from agentic_shared.domains.annotations.models import ChunkComment, CommentPointPayload
from agentic_shared.domains.retrieval.models import ChunkPointPayload
from agentic_shared.infrastructure.vector.core.payload import payload_page
from agentic_shared.infrastructure.vector.qdrant.enums import QdrantPointType
from agentic_shared.integrations.litellm.llm.content import extract_chat_completion_content
from agentic_shared.integrations.litellm.llm.messages import llm_system_user
from agentic_shared.integrations.litellm.llm.settings import LiteLLMChatSettings

from agentic_api.modules.annotations.deps import CommentGraphDeps
from agentic_api.modules.annotations.settings import get_module_settings
from agentic_api.modules.annotations.state import CommentState, CommentStateUpdate

_JSON_BLOCK = re.compile(r"\{[\s\S]*\}")

logger = logging.getLogger(__name__)


def _locale(state: CommentState) -> str:
    return state.get("locale") or DEFAULT_LOCALE


def _parse_moderation(content: str) -> dict[str, Any]:
    raw = content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    match = _JSON_BLOCK.search(raw)
    if not match:
        raise ValueError("No JSON in moderation response")
    parsed = json.loads(match.group())
    if not isinstance(parsed, dict):
        raise ValueError("Moderation JSON is not an object")
    return parsed


def _moderation_system_prompt(locale: str) -> str:
    language = LOCALE_LANGUAGE.get(locale, LOCALE_LANGUAGE[DEFAULT_LOCALE])
    reason_instruction = t("annotations.moderation.reason_instruction", locale, language=language)
    return t("annotations.moderation.system", locale, reason_instruction=reason_instruction)


async def moderate_node(state: CommentState, deps: CommentGraphDeps) -> CommentStateUpdate:
    """Rule checks + LLM guard against prompt injection and policy violations."""
    locale = _locale(state)
    module = get_module_settings()
    selected = state["selected_text"].strip()
    comment = state["comment_text"].strip()

    if not comment or len(comment) < module.comment_min_length:
        logger.debug("comment rejected too_short chunk_id=%s", state["chunk_id"])
        return {
            "approved": False,
            "rejection_reason": t("annotations.rejection.too_short", locale),
        }

    if len(comment) > module.comment_max_length:
        logger.debug("comment rejected too_long chunk_id=%s", state["chunk_id"])
        return {
            "approved": False,
            "rejection_reason": t(
                "annotations.rejection.too_long",
                locale,
                max=module.comment_max_length,
            ),
        }

    if looks_like_prompt_injection(comment):
        logger.warning("comment rejected injection chunk_id=%s", state["chunk_id"])
        return {
            "approved": False,
            "rejection_reason": t("annotations.rejection.injection", locale),
        }

    system = _moderation_system_prompt(locale)

    try:
        result = await deps.chat_client.chat_completion(
            llm_system_user(
                system,
                f"Selected excerpt:\n{selected}\n\nUser comment:\n{comment}",
            ),
            temperature=module.moderation_temperature,
            model=LiteLLMChatSettings().litellm_model,
        )
        content = extract_chat_completion_content(result)
        parsed = _parse_moderation(content)
        approved = bool(parsed.get("approved"))
        reason = (parsed.get("reason") or "").strip()
        if approved:
            logger.debug("comment moderation approved chunk_id=%s", state["chunk_id"])
            return {"approved": True, "moderation_notes": reason or "ok"}
        logger.info("comment moderation rejected chunk_id=%s", state["chunk_id"])
        return {
            "approved": False,
            "rejection_reason": reason or t("annotations.rejection.policy_default", locale),
        }
    except Exception:
        logger.exception("comment moderation failed chunk_id=%s", state["chunk_id"])
        return {
            "approved": False,
            "rejection_reason": t("annotations.rejection.moderation_failed", locale),
        }


async def persist_node(state: CommentState, deps: CommentGraphDeps) -> CommentStateUpdate:
    """Embed comment and attach to chunk metadata + indexed comment vector."""
    chunk_id = state["chunk_id"]
    tenant_id = state["tenant_id"]
    chunk_payload = ChunkPointPayload.model_validate(state["chunk_payload"])

    comment_id = str(uuid.uuid4())
    selected = state["selected_text"].strip()
    comment_text = state["comment_text"].strip()
    user_id = state["user_id"]
    created_at = datetime.now(UTC).isoformat()

    embed_text = f"Excerpt: {selected}\nComment: {comment_text}"
    vectors = await deps.embedding_client.embed([embed_text])
    vector = vectors[0]

    comment = ChunkComment(
        comment_id=comment_id,
        selected_text=selected,
        comment_text=comment_text,
        user_id=user_id,
        created_at=created_at,
    )

    comment_point_payload = CommentPointPayload(
        point_type=QdrantPointType.COMMENT,
        comment_id=comment_id,
        parent_chunk_id=chunk_id,
        tenant_id=chunk_payload.tenant_id or tenant_id,
        selected_text=selected,
        comment_text=comment_text,
        text=embed_text,
        user_id=user_id,
        created_at=created_at,
        doc_id=chunk_payload.doc_id,
        source_file=chunk_payload.source_file,
        page=payload_page(chunk_payload),
    )

    deps.comment_write.upsert(comment_id, comment_point_payload, vector=vector)
    deps.comment_write.append_to_chunk(chunk_id, comment, tenant_id=tenant_id)
    logger.info("comment persisted chunk_id=%s comment_id=%s", chunk_id, comment_id)

    return {"comment_id": comment_id, "approved": True}


def reject_node(state: CommentState) -> CommentStateUpdate:
    locale = _locale(state)
    return {
        "approved": False,
        "rejection_reason": state.get("rejection_reason")
        or t("annotations.rejection.default", locale),
    }
