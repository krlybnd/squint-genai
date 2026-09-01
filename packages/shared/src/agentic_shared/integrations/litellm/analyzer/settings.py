import json
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import NoDecode

from agentic_shared.integrations.core.settings import IntegrationSettings

DEFAULT_ANALYZER_ENTITIES: tuple[str, ...] = (
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IBAN_CODE",
    "CREDIT_CARD",
    "IP_ADDRESS",
)


class AnalyzerSettings(IntegrationSettings):
    """Analyzer sidecar (Presidio analyzer; default Compose stack)."""

    title: str = Field(
        default="analyzer",
        description="Readiness/log label for the analyzer client.",
    )
    analyzer_api_base: str = Field(
        default="http://localhost:5002",
        description="Analyzer base URL (host or docker DNS). Env: ANALYZER_API_BASE.",
    )
    analyzer_entities: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(DEFAULT_ANALYZER_ENTITIES),
        description=(
            "Entity types Presidio may detect. Leaving this open lets DATE_TIME and the US_* "
            "recognizers claim fragments of identifiers, which splits IBANs and tax numbers "
            "into several tokens. Empty means every built-in recognizer. "
            "Env: ANALYZER_ENTITIES (JSON list or comma-separated)."
        ),
    )
    analyzer_score_threshold: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description=("Drop analyzer hits below this confidence. Env: ANALYZER_SCORE_THRESHOLD."),
    )
    analyzer_allow_list: Annotated[list[str], NoDecode] = Field(
        default_factory=list,
        description=(
            "Regex patterns for terms never treated as PII — code names, legal-entity "
            "prefixes and other corpus vocabulary the NER model otherwise reads as person "
            "names. A pattern also clears the longer span containing it, so `Kamu` clears "
            "`Kamuhold Beruházási Zrt.`. "
            "Env: ANALYZER_ALLOW_LIST (JSON list or comma-separated)."
        ),
    )

    @field_validator("analyzer_entities", "analyzer_allow_list", mode="before")
    @classmethod
    def parse_term_list(cls, value: object) -> object:
        """Accept JSON lists as well as the comma-separated form used in ``.env``."""
        if not isinstance(value, str):
            return value
        trimmed = value.strip()
        if not trimmed:
            return []
        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            return [item.strip() for item in trimmed.split(",") if item.strip()]

    def analyze_payload(self, text: str, *, language: str) -> dict[str, object]:
        """Presidio ``/analyze`` body carrying the configured detection limits."""
        payload: dict[str, object] = {"text": text, "language": language}
        if self.analyzer_entities:
            payload["entities"] = list(self.analyzer_entities)
        if self.analyzer_score_threshold > 0.0:
            payload["score_threshold"] = self.analyzer_score_threshold
        if self.analyzer_allow_list:
            payload["allow_list"] = list(self.analyzer_allow_list)
            payload["allow_list_match"] = "regex"
        return payload


__all__ = ["DEFAULT_ANALYZER_ENTITIES", "AnalyzerSettings"]
