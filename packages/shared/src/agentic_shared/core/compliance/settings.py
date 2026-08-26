from agentic_shared.core.settings.base import EnvSettings


class ComplianceSettings(EnvSettings):
    """Global compliance toggles and retention defaults."""

    compliance_enabled: bool = False
    audit_log_enabled: bool = True
    ai_transparency_enabled: bool = True
    ai_system_name: str = "agentic-rag-eval"
    ai_risk_tier: str = "limited"
    ai_human_oversight: bool = True
    document_retention_days: int = 365
    chat_retention_days: int = 90
    audit_retention_days: int = 730
