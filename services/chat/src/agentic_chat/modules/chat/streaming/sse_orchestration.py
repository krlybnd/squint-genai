"""Orchestration-level SSE (session title, stream start) — graph steps in sse_reasoning."""

from agentic_shared.core.i18n import t

from agentic_chat.modules.chat.enums import ReasoningStatus, ReasoningStep
from agentic_chat.modules.chat.streaming.sse_events import (
    ErrorEventData,
    ReasoningEventData,
    RunEventData,
    SessionEventData,
    sse_error,
    sse_reasoning,
    sse_run,
    sse_session,
)


def sse_session_not_found(locale: str) -> str:
    return sse_error(ErrorEventData(message=t("error.session_not_found", locale)))


def sse_no_checkpoint(locale: str) -> str:
    return sse_error(ErrorEventData(message=t("error.no_checkpoint", locale)))


def sse_run_started(run_id: str) -> str:
    return sse_run(RunEventData(run_id=run_id))


def sse_run_replay(run_id: str, checkpoint_id: str) -> str:
    return sse_run(
        RunEventData(run_id=run_id, replay=True, checkpoint_id=checkpoint_id),
    )


def sse_stream_start(locale: str) -> str:
    return sse_reasoning(
        ReasoningEventData(
            step=ReasoningStep.START,
            message=t("reasoning.start", locale),
            status=ReasoningStatus.ACTIVE,
        ),
    )


def sse_stream_retry(locale: str) -> str:
    return sse_reasoning(
        ReasoningEventData(
            step=ReasoningStep.START,
            message=t("reasoning.retry", locale),
            status=ReasoningStatus.ACTIVE,
        ),
    )


def sse_title_active(locale: str) -> str:
    return sse_reasoning(
        ReasoningEventData(
            step=ReasoningStep.TITLE,
            message=t("reasoning.title_active", locale),
            status=ReasoningStatus.ACTIVE,
        ),
    )


def sse_title_done(locale: str, title: str) -> str:
    return sse_reasoning(
        ReasoningEventData(
            step=ReasoningStep.TITLE,
            message=t("reasoning.title_done", locale, title=title),
            status=ReasoningStatus.DONE,
        ),
    )


def sse_session_title_updated(session_id: str, title: str) -> str:
    return sse_session(SessionEventData(session_id=session_id, title=title))
