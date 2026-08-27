"""Golden dataset loader for eval suites."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

DATASET_PATH = Path(__file__).resolve().parent / "dataset.json"

KNOWN_SOURCE_FILES = frozenset(
    {
        "attention-is-all-you-need.pdf",
        "rag-lewis-2020.pdf",
        "us-constitution.pdf",
        "nasa-fy2025-mission-fact-sheets.pdf",
        "nist-ai-rmf-1.0.pdf",
    }
)


@dataclass(frozen=True, slots=True)
class Golden:
    input: str
    expected_output: str
    expected_source_file: str | None = None
    expected_snippet: str | None = None
    expect_abstention: bool = False


def load_goldens(path: Path = DATASET_PATH) -> list[Golden]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    goldens: list[Golden] = []
    for item in raw:
        expect_abstention = bool(item.get("expect_abstention", False))
        source_file = item.get("expected_source_file")
        if expect_abstention:
            if source_file is not None:
                msg = "abstention goldens must not set expected_source_file"
                raise ValueError(msg)
        elif not source_file or source_file not in KNOWN_SOURCE_FILES:
            msg = f"missing or unknown expected_source_file: {source_file!r}"
            raise ValueError(msg)
        goldens.append(
            Golden(
                input=item["input"],
                expected_output=item["expected_output"],
                expected_source_file=source_file,
                expected_snippet=item.get("expected_snippet"),
                expect_abstention=expect_abstention,
            )
        )
    return goldens
