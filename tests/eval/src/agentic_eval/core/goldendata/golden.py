"""Typed goldens shared by retrieval and generation experiments."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

from agentic_eval.core.goldendata.settings import DEFAULT_SOURCE_FILES, GoldenSettings


class _GoldenBase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    input: str
    expected_output: str
    expected_snippet: str | None = None


class LabeledGolden(_GoldenBase):
    expect_abstention: Literal[False] = False
    expected_source_file: str

    @field_validator("expected_source_file")
    @classmethod
    def _known_source(cls, value: str, info: ValidationInfo) -> str:
        allowed: Sequence[str] = DEFAULT_SOURCE_FILES
        if info.context and "known_source_files" in info.context:
            allowed = info.context["known_source_files"]
        if value not in allowed:
            raise ValueError(f"unknown source file: {value}")
        return value


class AbstentionGolden(_GoldenBase):
    expect_abstention: Literal[True]
    expected_source_file: None = None


Golden = LabeledGolden | AbstentionGolden


def case_name(index: int, text: str) -> str:
    label = text if len(text) <= 72 else f"{text[:69]}..."
    return f"{index:02d}:{label}"


def load_goldens(
    path: Path | None = None,
    *,
    settings: GoldenSettings | None = None,
) -> list[Golden]:
    cfg = settings if settings is not None else GoldenSettings()
    dataset = path if path is not None else cfg.dataset_path
    raw = json.loads(dataset.read_text(encoding="utf-8"))
    return [_parse_golden(item, known_source_files=cfg.known_source_files) for item in raw]


def labeled_goldens(goldens: list[Golden]) -> list[LabeledGolden]:
    return [item for item in goldens if isinstance(item, LabeledGolden)]


def abstention_goldens(goldens: list[Golden]) -> list[AbstentionGolden]:
    return [item for item in goldens if isinstance(item, AbstentionGolden)]


def _parse_golden(item: object, *, known_source_files: Sequence[str]) -> Golden:
    if isinstance(item, dict) and item.get("expect_abstention"):
        return AbstentionGolden.model_validate(item)
    return LabeledGolden.model_validate(
        item,
        context={"known_source_files": known_source_files},
    )
