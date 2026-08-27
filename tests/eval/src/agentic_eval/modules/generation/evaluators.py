"""Refusal heuristic for abstention goldens (not a DeepEval metric)."""

from __future__ import annotations

from collections.abc import Sequence

from agentic_eval.modules.generation.settings import DEFAULT_REFUSAL_MARKERS


def looks_like_refusal(
    answer: str,
    markers: Sequence[str] = DEFAULT_REFUSAL_MARKERS,
) -> bool:
    """True when the generator abstained instead of answering from context."""
    text = answer.lower()
    return any(marker in text for marker in markers)
