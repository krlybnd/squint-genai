from __future__ import annotations

from typing import Literal

from agentic_eval.core.golden.base import Golden


class AbstentionGolden(Golden):
    expect_abstention: Literal[True]
    expected_source_file: None = None

    @classmethod
    def matches(cls, raw: object) -> bool:
        return isinstance(raw, dict) and bool(raw.get("expect_abstention"))
