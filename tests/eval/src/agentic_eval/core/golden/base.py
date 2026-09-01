"""Shared golden model. Subclasses own ``matches`` / ``parse`` (open for new kinds)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Self

from pydantic import BaseModel, ConfigDict, ValidationInfo


class Golden(BaseModel, ABC):
    model_config = ConfigDict(extra="ignore")

    input: str
    expected_output: str

    @classmethod
    def allowed_sources(cls, info: ValidationInfo) -> Sequence[str]:
        from agentic_eval.core.golden.settings import GoldenSettings

        if info.context and "known_source_files" in info.context:
            return info.context["known_source_files"]
        sources = GoldenSettings.model_fields["known_source_files"].default
        if not isinstance(sources, tuple):
            raise TypeError("GoldenSettings.known_source_files default must be a tuple")
        return sources

    @classmethod
    @abstractmethod
    def matches(cls, raw: object) -> bool:
        """True when this class should parse ``raw``."""

    @classmethod
    def parse(cls, raw: object, *, known_source_files: Sequence[str]) -> Self:
        return cls.model_validate(
            raw,
            context={"known_source_files": known_source_files},
        )

    def case_name(self, index: int) -> str:
        label = self.input if len(self.input) <= 72 else f"{self.input[:69]}..."
        return f"{index:02d}:{label}"
