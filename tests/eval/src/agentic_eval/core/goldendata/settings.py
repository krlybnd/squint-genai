from __future__ import annotations

from pathlib import Path

from agentic_shared.core.settings.module import ModuleSettings
from pydantic_settings import SettingsConfigDict

# tests/eval/src/agentic_eval/core/goldendata/settings.py → parents[4]=tests/eval
EVAL_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATASET_PATH = EVAL_ROOT / "dataset.json"

DEFAULT_SOURCE_FILES: tuple[str, ...] = (
    "attention-is-all-you-need.pdf",
    "rag-lewis-2020.pdf",
    "us-constitution.pdf",
    "nasa-fy2025-mission-fact-sheets.pdf",
    "nist-ai-rmf-1.0.pdf",
)


class GoldenSettings(ModuleSettings):
    """Dataset path and allowed source files. Override per run via ``EVAL_GOLDEN_*``."""

    model_config = SettingsConfigDict(env_prefix="EVAL_GOLDEN_", extra="ignore", env_file=None)

    dataset_path: Path = DEFAULT_DATASET_PATH
    known_source_files: tuple[str, ...] = DEFAULT_SOURCE_FILES
