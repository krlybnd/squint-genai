"""Live generation eval: ask the running chat API, then score with DeepEval."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from sys import stdout

_TESTS = Path(__file__).resolve().parents[1]
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from deepeval.config.settings import get_settings
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, GEval
from deepeval.models import OpenAIModel
from deepeval.test_case import LLMTestCase, SingleTurnParams

from agentic_eval.core.deepeval import AbstentionMetric, RequiredPhrasesMetric, evaluate
from agentic_eval.core.golden import GoldenDataset, GoldenSettings
from agentic_eval.core.settings import eval_env_file
from generation.product import Product
from generation.settings import REPORTS_DIR, GenerationSettings


def main() -> int:
    # --- Prerequisites -------------------------------------------------------
    # Needs .env (LiteLLM key, chat/api URLs). Do not `source` it — bash mangles JSON.
    # Make creates the markdown reports dir; crash here if it is missing.
    if eval_env_file() is None:
        stdout.write(
            "Live eval needs tests/eval/.env — cp tests/eval/.env.example tests/eval/.env\n"
        )
        stdout.flush()
        return 2
    settings = GenerationSettings.load()
    if not REPORTS_DIR.is_dir():
        raise FileNotFoundError(REPORTS_DIR)

    api_key = settings.core.proxy_api_key.strip()
    if not api_key:
        stdout.write(
            "LiteLLM proxy API key is empty. Set LITELLM_MASTER_KEY or "
            "EVAL_SUT_LITELLM_API_KEY in tests/eval/.env.\n"
        )
        stdout.flush()
        return 2

    # --- Judge LLM -----------------------------------------------------------
    # Scoring uses LiteLLM `judge` (gpt-4o), not the chat/generate model.
    # Retry lives on DeepEval's Settings singleton so a 429 is not a quality FAIL.
    live = get_settings()
    live.DEEPEVAL_RETRY_MAX_ATTEMPTS = settings.deepeval.max_attempts
    live.DEEPEVAL_RETRY_INITIAL_SECONDS = settings.deepeval.initial_seconds
    live.DEEPEVAL_RETRY_CAP_SECONDS = settings.deepeval.cap_seconds
    judge = OpenAIModel(
        model=settings.judge.model.strip() or "judge",
        api_key=api_key,
        base_url=settings.core.openai_compatible_base_url,
    )

    # --- Goldens -------------------------------------------------------------
    # labeled = expected answer is in the dossiers
    # abstention = deliberate "I don't know / not in the corpus"
    golden_settings = GoldenSettings.investigation()
    goldens = GoldenDataset.load(golden_settings)
    labeled = goldens.labeled
    abstention = goldens.abstention
    markers = settings.gates.refusal_markers
    gen = settings.gates

    # --- Product: running chat SSE ------------------------------------------
    # Catalog check (three dossiers indexed), then each question on its own
    # ephemeral session. Product strips vault marks before the judge.
    async def run_app() -> tuple[list[tuple[str, list[str]]], list[tuple[str, list[str]]]]:
        async with Product(settings.core) as sut:
            await sut.assert_ready()
            await sut.assert_catalog(golden_settings.known_source_files)
            labeled_out = await sut.ask_many(
                [item.input for item in labeled],
                description=f"chat SSE ({len(labeled)} labeled)",
            )
            abstention_out = await sut.ask_many(
                [item.input for item in abstention],
                description=f"chat SSE ({len(abstention)} abstention)",
            )
            return labeled_out, abstention_out

    labeled_out, abstention_out = asyncio.run(run_app())

    ok = True
    # --- DeepEval: labeled ---------------------------------------------------
    # Correctness = golden expected_output; Faithfulness = retrieved chunks;
    # Required phrases = identifiers verbatim; Abstention = must not refuse.
    if labeled:
        report = evaluate(
            [
                LLMTestCase(
                    input=item.input,
                    actual_output=answer,
                    expected_output=item.expected_output,
                    retrieval_context=ctx,
                    tags=["labeled"],
                    metadata={"required_phrases": list(item.required_phrases)},
                )
                for item, (answer, ctx) in zip(labeled, labeled_out, strict=True)
            ],
            [
                GEval(
                    name="Correctness",
                    evaluation_steps=[
                        "Check whether the facts in 'actual output' contradict "
                        "any facts in 'expected output'.",
                        "Heavily penalize omission of key entities, identifiers, "
                        "amounts, or yes/no conclusions from 'expected output'.",
                        "Extra wording is acceptable when the key facts are present.",
                    ],
                    evaluation_params=[
                        SingleTurnParams.ACTUAL_OUTPUT,
                        SingleTurnParams.EXPECTED_OUTPUT,
                    ],
                    threshold=gen.correctness_threshold,
                    model=judge,
                    async_mode=False,
                ),
                FaithfulnessMetric(
                    threshold=gen.faithfulness_threshold,
                    model=judge,
                    async_mode=False,
                ),
                AnswerRelevancyMetric(
                    threshold=gen.answer_relevancy_threshold, model=judge, async_mode=False
                ),
                RequiredPhrasesMetric(),
                AbstentionMetric(markers=markers),
            ],
            identifier="investigation-generation",
            reports_dir=REPORTS_DIR,
            max_concurrent=settings.judge.max_concurrency,
            throttle_seconds=settings.judge.throttle_seconds,
        )
        ok = all(item.success for item in report.test_results)

    # --- DeepEval: abstention ------------------------------------------------
    # Separate call, AbstentionMetric only — Faithfulness must not run on "cannot find".
    if abstention:
        report = evaluate(
            [
                LLMTestCase(
                    input=item.input,
                    actual_output=answer,
                    expected_output=item.expected_output,
                    tags=["abstention"],
                )
                for item, (answer, _) in zip(abstention, abstention_out, strict=True)
            ],
            [AbstentionMetric(markers=markers)],
            identifier="investigation-abstention",
            reports_dir=REPORTS_DIR,
            max_concurrent=settings.judge.max_concurrency,
            throttle_seconds=settings.judge.throttle_seconds,
        )
        ok = ok and all(item.success for item in report.test_results)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
