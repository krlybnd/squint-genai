"""Tier 1 live gate: investigation dossier retrieval IR (indexed resources/eval/)."""

from agentic_eval.core.reports import write_retrieval_report
from agentic_eval.modules.retrieval.experiment import RetrievalExperiment
from agentic_eval.modules.retrieval.metrics import RetrievalScores
from agentic_eval.profiles import EvalProfile, get_profile
from suit.settings import SuitSettings


def test_investigation_retrieval_ir_meets_thresholds(suit: SuitSettings) -> None:
    """Labeled investigation goldens must retrieve expected dossier from live Qdrant.

    Corpus: ``resources/eval/investigation-dossier-*.md`` (or .pdf after pandoc).
    Metrics: Recall@k, Precision@k, Hit Rate@k, MRR, nDCG@k — no judge LLM.
    Gate: investigation profile minimums (Recall@5 ≥ 0.90, Precision@5 ≥ 0.85).
    """
    profile = get_profile(EvalProfile.investigation)
    experiment = RetrievalExperiment(name="investigation_retrieval_ir")
    gate = suit.retrieval.model_copy(update={"minimums": profile.retrieval_minimums})

    report = experiment.run(
        suit,
        suit.sut,
        golden_settings=profile.golden,
        stem_match=profile.retrieval_stem_match,
    )
    report.print()
    averages = report.averages()
    assert averages is not None, "investigation retrieval produced no scores"
    scores = RetrievalScores.model_validate(
        {name: float(averages.scores[name]) for name in RetrievalScores.model_fields}
    )
    write_retrieval_report(report, scores, gate, profile.retrieval_report)
    scores.assert_at_least(profile.retrieval_minimums)
    print(
        f"  investigation retrieval k={gate.k}: "
        f"recall={scores.recall_at_k:.2f}>={profile.retrieval_minimums.recall_at_k:.2f} "
        f"prec={scores.precision_at_k:.2f}>={profile.retrieval_minimums.precision_at_k:.2f} "
        f"balanced gate pass"
    )
