import asyncio
import os

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from goldens import Golden, load_goldens
from metrics import rag_metrics
from rag_app import answer_question

pytestmark = [
    pytest.mark.eval,
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("EVAL_MODE") != "live",
        reason="RAG eval runs the real stack + judge LLM (make eval-live)",
    ),
]

GENERATION_GOLDENS = [golden for golden in load_goldens() if not golden.expect_abstention]


@pytest.mark.parametrize("golden", GENERATION_GOLDENS, ids=lambda g: g.input)
def test_rag_quality(golden: Golden) -> None:
    answer, contexts = asyncio.run(answer_question(golden.input))
    assert_test(
        LLMTestCase(
            input=golden.input,
            actual_output=answer,
            expected_output=golden.expected_output,
            retrieval_context=contexts,
        ),
        rag_metrics(),
    )
