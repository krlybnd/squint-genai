import asyncio
import os
from pathlib import Path

import pytest
from deepeval import assert_test
from deepeval.dataset import EvaluationDataset, Golden
from deepeval.test_case import LLMTestCase

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

dataset = EvaluationDataset()
dataset.add_goldens_from_json_file(file_path=str(Path(__file__).parent / "dataset.json"))


@pytest.mark.parametrize("golden", dataset.goldens, ids=lambda g: g.input)
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
