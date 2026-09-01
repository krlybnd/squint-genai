from __future__ import annotations

from pathlib import Path

from agentic_shared.core.settings.module import ModuleSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from agentic_eval.core.settings import EVAL_ROOT


class GoldenSettings(ModuleSettings):
    """Dataset path and allowed source files. Override per run via ``EVAL_GOLDEN_*``."""

    model_config = SettingsConfigDict(env_prefix="EVAL_GOLDEN_", extra="ignore", env_file=None)

    dataset_path: Path = Field(
        default=EVAL_ROOT / "dataset.json",
        description="Golden dataset JSON. Env: EVAL_GOLDEN_DATASET_PATH.",
    )
    known_source_files: tuple[str, ...] = Field(
        default=(
            "attention-is-all-you-need.pdf",
            "rag-lewis-2020.pdf",
            "us-constitution.pdf",
            "nasa-fy2025-mission-fact-sheets.pdf",
            "nist-ai-rmf-1.0.pdf",
        ),
        description=(
            "Source files a golden may reference; anything else fails validation. "
            "Env: EVAL_GOLDEN_KNOWN_SOURCE_FILES."
        ),
    )

    @classmethod
    def investigation(cls) -> InvestigationGoldenSettings:
        return InvestigationGoldenSettings()


class InvestigationGoldenSettings(GoldenSettings):
    dataset_path: Path = Field(
        default=EVAL_ROOT / "dataset-investigation.json",
        description="Investigation golden dataset JSON. Env: EVAL_GOLDEN_DATASET_PATH.",
    )
    known_source_files: tuple[str, ...] = Field(
        default=(
            "investigation-dossier-alpha.md",
            "investigation-dossier-beta.md",
            "investigation-dossier-gamma-decoy.md",
            "investigation-dossier-alpha.pdf",
            "investigation-dossier-beta.pdf",
            "investigation-dossier-gamma-decoy.pdf",
        ),
        description=(
            "Investigation dossiers a golden may reference (md names + indexed pdf stems). "
            "Env: EVAL_GOLDEN_KNOWN_SOURCE_FILES."
        ),
    )
