from pydantic import Field

from agentic_shared.core.settings.base import EnvSettings


class ComplianceSettings(EnvSettings):
    """Global compliance toggles and retention defaults."""

    compliance_enabled: bool = Field(
        default=False,
        description="Master switch for compliance adapters (audit, retention hooks).",
    )
    audit_log_enabled: bool = Field(
        default=True,
        description="When compliance is on, emit audit events for sensitive actions.",
    )
    ai_transparency_enabled: bool = Field(
        default=True,
        description="Expose AI system metadata (name, risk tier, oversight) to clients.",
    )
    ai_system_name: str = Field(
        default="agentic-rag-eval",
        description="Public name of this AI system for transparency disclosures.",
    )
    ai_risk_tier: str = Field(
        default="limited",
        description="Declared EU AI Act-style risk tier label (informational).",
    )
    ai_human_oversight: bool = Field(
        default=True,
        description="Whether human oversight is declared for this AI system.",
    )
    document_retention_days: int = Field(
        default=365,
        description="Default retention window for stored documents (days).",
    )
    chat_retention_days: int = Field(
        default=90,
        description="Default retention window for chat sessions/messages (days).",
    )
    audit_retention_days: int = Field(
        default=730,
        description="Default retention window for audit records (days).",
    )
