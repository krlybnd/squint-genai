"""Investigation golden dataset settings."""

from __future__ import annotations

from agentic_eval.core.goldendata.settings import EVAL_ROOT

INVESTIGATION_DATASET_PATH = EVAL_ROOT / "dataset-investigation.json"
GUARDRAILS_CASES_PATH = EVAL_ROOT / "guardrails-cases.json"

INVESTIGATION_SOURCE_FILES: tuple[str, ...] = (
    "investigation-dossier-alpha.md",
    "investigation-dossier-beta.md",
    "investigation-dossier-gamma-decoy.md",
)

# PDF names after pandoc conversion — accepted alongside .md in goldens.
INVESTIGATION_SOURCE_FILES_PDF: tuple[str, ...] = tuple(
    name.replace(".md", ".pdf") for name in INVESTIGATION_SOURCE_FILES
)
