from __future__ import annotations

from typing import Literal

from pydantic import ValidationInfo, field_validator

from agentic_eval.core.golden.base import Golden


class LabeledGolden(Golden):
    expect_abstention: Literal[False] = False
    expected_source_file: str
    expected_source_files: tuple[str, ...] | None = None
    required_phrases: tuple[str, ...] = ()

    @classmethod
    def matches(cls, raw: object) -> bool:
        return isinstance(raw, dict) and not raw.get("expect_abstention")

    @property
    def relevant_sources(self) -> tuple[str, ...]:
        if self.expected_source_files:
            return self.expected_source_files
        return (self.expected_source_file,)

    @field_validator("expected_source_file")
    @classmethod
    def _known_source(cls, value: str, info: ValidationInfo) -> str:
        if value not in cls.allowed_sources(info):
            raise ValueError(f"unknown source file: {value}")
        return value

    @field_validator("expected_source_files")
    @classmethod
    def _known_sources(
        cls,
        value: tuple[str, ...] | None,
        info: ValidationInfo,
    ) -> tuple[str, ...] | None:
        if value is None:
            return value
        allowed = set(cls.allowed_sources(info))
        unknown = [item for item in value if item not in allowed]
        if unknown:
            raise ValueError(f"unknown source file: {unknown[0]}")
        return value
