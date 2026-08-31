"""Typed goldens: ``Golden`` kinds + ``GoldenDataset`` loader."""

from agentic_eval.core.golden.abstention import AbstentionGolden
from agentic_eval.core.golden.base import Golden
from agentic_eval.core.golden.dataset import GoldenDataset
from agentic_eval.core.golden.labeled import LabeledGolden
from agentic_eval.core.golden.settings import GoldenSettings, InvestigationGoldenSettings

__all__ = [
    "AbstentionGolden",
    "Golden",
    "GoldenDataset",
    "GoldenSettings",
    "InvestigationGoldenSettings",
    "LabeledGolden",
]
