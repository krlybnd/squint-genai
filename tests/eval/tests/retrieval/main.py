"""Live retrieval eval: search the running api, then score with pydantic-evals."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from sys import stdout

_TESTS = Path(__file__).resolve().parents[1]
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from pydantic_evals import Case, Dataset

from agentic_eval.core.golden import GoldenDataset, GoldenSettings
from agentic_eval.core.pydantic_evals import RetrievalIR, evaluate
from agentic_eval.core.settings import eval_env_file
from retrieval.product import Product
from retrieval.settings import RetrievalSettings


def main() -> int:
    # --- Prerequisites -------------------------------------------------------
    # Needs .env (chat/api URLs, auth). Do not `source` it — bash mangles JSON.
    if eval_env_file() is None:
        stdout.write(
            "Live eval needs tests/eval/.env — cp tests/eval/.env.example tests/eval/.env\n"
        )
        stdout.flush()
        return 2
    settings = RetrievalSettings.load()

    # --- Goldens -------------------------------------------------------------
    # Labeled only: IR needs a relevant-dossier set. Abstention is not an IR case.
    golden_settings = GoldenSettings.investigation()
    labeled = GoldenDataset.load(golden_settings).labeled
    k = settings.k

    dataset = Dataset(
        name="investigation_retrieval_ir",
        cases=[
            Case(
                name=item.case_name(index),
                inputs=item.input,
                expected_output=list(item.relevant_sources),
            )
            for index, item in enumerate(labeled, start=1)
        ],
        evaluators=[RetrievalIR(k=k)],
    )

    # --- Product: running api search ----------------------------------------
    # Catalog check + evaluate on the same loop (httpx client).
    # Native Dataset.evaluate + report.print. RetrievalIR is the core extension.
    async def run():
        async with Product(settings.core, top_k=k) as sut:
            await sut.assert_catalog(golden_settings.known_source_files)
            return await evaluate(
                dataset,
                sut.search,
                name="investigation-retrieval",
                max_concurrency=settings.core.max_concurrency,
            )

    report = asyncio.run(run())

    averages = report.averages()
    if averages is None:
        stdout.write("investigation retrieval produced no scores\n")
        stdout.flush()
        return 1

    # --- Gates (suite settings, not core) ------------------------------------
    missed = {
        name: {"actual": float(averages.scores[name]), "min": minimum}
        for name, minimum in settings.minimums.model_dump().items()
        if float(averages.scores[name]) < minimum
    }
    if missed:
        stdout.write("retrieval gates missed: " + str(missed) + "\n")
        stdout.flush()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
