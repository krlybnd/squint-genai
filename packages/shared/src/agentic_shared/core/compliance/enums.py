from enum import StrEnum


class AuditEventCategory(StrEnum):
    """Security and privacy audit event categories (NIS2 / GDPR accountability)."""

    AUTH = "auth"
    ACCESS = "access"
    DATA_CHANGE = "data_change"
    DATA_EXPORT = "data_export"
    DATA_ERASURE = "data_erasure"
    AI_INTERACTION = "ai_interaction"
    INCIDENT = "incident"
    CONFIG_CHANGE = "config_change"


class DataSubjectRequestType(StrEnum):
    """GDPR data-subject rights (Articles 15–20)."""

    ACCESS = "access"
    RECTIFICATION = "rectification"
    ERASURE = "erasure"
    RESTRICTION = "restriction"
    PORTABILITY = "portability"
    OBJECTION = "objection"


class IncidentSeverity(StrEnum):
    """NIS2-aligned incident severity for early notification workflows."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AiRiskTier(StrEnum):
    """EU AI Act risk classification placeholder (operator-defined mapping)."""

    MINIMAL = "minimal"
    LIMITED = "limited"
    HIGH = "high"
    UNACCEPTABLE = "unacceptable"
