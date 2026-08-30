"""Investigation corpus — DeepEval generation gate (LLM-as-judge)."""

from __future__ import annotations

import sys

from agentic_eval.modules.generation.runner import run_generation_gate
from agentic_eval.profiles import EvalProfile, get_profile
from agentic_eval.settings import EvalMode
from suit.qdrant import require_qdrant_collection
from suit.settings import eval_env_file, load_suit_settings


def main() -> int:
    if eval_env_file() is None:
        print(
            "Live eval needs tests/eval/.env — cp tests/eval/.env.example tests/eval/.env",
            file=sys.stderr,
        )
        return 2
    suit = load_suit_settings()
    if suit.mode is not EvalMode.live:
        print("Set EVAL_MODE=live in tests/eval/.env", file=sys.stderr)
        return 2
    require_qdrant_collection(url=suit.sut.qdrant_url, collection=suit.sut.qdrant_collection)
    profile = get_profile(EvalProfile.investigation)
    return run_generation_gate(suit, profile)


if __name__ == "__main__":
    raise SystemExit(main())
