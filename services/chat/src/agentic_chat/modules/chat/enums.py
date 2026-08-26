from enum import StrEnum


class ReasoningStatus(StrEnum):
    ACTIVE = "active"
    DONE = "done"


class ReasoningStep(StrEnum):
    START = "start"
    TITLE = "title"
    PLAN = "plan"
    GUARD = "guard"
    REWRITE = "rewrite"
    RETRIEVE = "retrieve"
    GENERATE = "generate"


class SseEventType(StrEnum):
    RUN = "run"
    REASONING = "reasoning"
    STATUS = "status"
    TOKEN = "token"
    SESSION = "session"
    DONE = "done"
    ERROR = "error"
