"""Unit tests for chapter3/retrieval-pipeline/stage_evaluator.py.

Covers the atomic metric primitives (precision@k, recall@k, NDCG@k, MRR),
single-stage evaluation, multi-stage pipeline evaluation, marginal improvement,
diminishing-returns detection, best-combination selection, and the boundary /
edge cases (empty results, perfect retrieval, no relevant docs found, missing
query results). All tests are deterministic and make no network or model calls.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

# Make chapter3/retrieval-pipeline importable.
ch3_dir = Path(__file__).resolve().parent.parent / "chapter3" / "retrieval-pipeline"
if str(ch3_dir) not in sys.path:
    sys.path.insert(0, str(ch3_dir))

from stage_evaluator import (  # noqa: E402
    RetrievalStageEvaluator,
    StageContributionReport,
    StageMetrics,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _result(doc_id: str, score: float, query_id: str = "q1") -> dict:
    """A single ranked result dict (score-ordered)."""
    return {"doc_id": doc_id, "score": score, "query_id": query_id}


def _ranked(doc_id: str, rank: int, query_id: str = "q1") -> dict:
    """A single ranked result dict (rank-ordered)."""
    return {"doc_id": doc_id, "rank": rank, "query_id": query_id}


def _gold_q1() -> set[str]:
    return {"d1", "d3", "d5"}


# --------------------------------------------------------------------------- #
# Precision@k
# --------------------------------------------------------------------------- #
def test_precision_at_k_basic():
    ranked = ["d1", "d2", "d3", "d4"]
    gold = {"d1", "d3"}
    # top-2 hits: d1 -> 1 relevant / 2 = 0.5
    assert RetrievalStageEvaluator.compute_precision_at_k(ranked, gold, 2) == 0.5
    # top-4 hits: d1, d3 -> 2 relevant / 4 = 0.5
    assert RetrievalStageEvaluator.compute_precision_at_k(ranked, gold, 4) == 0.5


def test_precision_at_k_perfect_and_empty():
    gold = {"d1", "d2"}
    assert RetrievalStageEvaluator.compute_precision_at_k(["d1", "d2"], gold, 2) == 1.0
    # No hits at all.
    assert RetrievalStageEvaluator.compute_precision_at_k(["d9", "d8"], gold, 2) == 0.0
    # k <= 0 is defined as 0.0.
    assert RetrievalStageEvaluator.compute_precision_at_k(["d1"], gold, 0) == 0.0


def test_precision_at_k_k_larger_than_list():
    # Only 2 results but k=10 -> denominator is k, so 2/10.
    ranked = ["d1", "d2"]
    gold = {"d1", "d2"}
    assert RetrievalStageEvaluator.compute_precision_at_k(ranked, gold, 10) == pytest.approx(0.2)


# --------------------------------------------------------------------------- #
# Recall@k
# --------------------------------------------------------------------------- #
def test_recall_at_k_basic():
    ranked = ["d1", "d2", "d3"]
    gold = {"d1", "d3", "d5"}
    # top-3 captures d1, d3 -> 2/3.
    assert RetrievalStageEvaluator.compute_recall_at_k(ranked, gold, 3) == pytest.approx(2 / 3)


def test_recall_at_k_no_gold_returns_zero():
    # Matches evaluate.recall_at_k: empty gold -> 0.0 (not a division error).
    assert RetrievalStageEvaluator.compute_recall_at_k(["d1", "d2"], set(), 5) == 0.0


def test_recall_at_k_full_recall():
    ranked = ["d1", "d2", "d3"]
    gold = {"d1", "d2", "d3"}
    assert RetrievalStageEvaluator.compute_recall_at_k(ranked, gold, 3) == 1.0
    # k larger than list still full recall.
    assert RetrievalStageEvaluator.compute_recall_at_k(ranked, gold, 10) == 1.0


# --------------------------------------------------------------------------- #
# NDCG@k
# --------------------------------------------------------------------------- #
def test_ndcg_at_k_perfect_ordering():
    gold = {"d1", "d2", "d3"}
    # All relevant docs in the top 3, in order -> NDCG@3 == 1.0.
    assert RetrievalStageEvaluator.compute_ndcg_at_k(["d1", "d2", "d3"], gold, 3) == pytest.approx(1.0)


def test_ndcg_at_k_imperfect_ordering():
    gold = {"d1", "d2"}
    # ranked = [d1, d3, d2]; top-3: relevant at ranks 1 and 3.
    # dcg = 1/log2(2) + 1/log2(4) = 1 + 0.5 = 1.5
    # idcg = 1/log2(2) + 1/log2(3) = 1 + 1/1.58496 = 1 + 0.63093 = 1.63093
    dcg = 1.0 / math.log2(2) + 1.0 / math.log2(4)
    idcg = 1.0 / math.log2(2) + 1.0 / math.log2(3)
    expected = dcg / idcg
    assert RetrievalStageEvaluator.compute_ndcg_at_k(
        ["d1", "d3", "d2"], gold, 3
    ) == pytest.approx(expected)


def test_ndcg_at_k_no_relevant_returns_zero():
    assert RetrievalStageEvaluator.compute_ndcg_at_k(["d1", "d2"], set(), 5) == 0.0
    # No gold hit in top-k.
    assert RetrievalStageEvaluator.compute_ndcg_at_k(["d9", "d8"], {"d1"}, 2) == 0.0


# --------------------------------------------------------------------------- #
# MRR
# --------------------------------------------------------------------------- #
def test_mrr_first_relevant():
    gold = {"d2"}
    assert RetrievalStageEvaluator.compute_mrr(["d1", "d2", "d3"], gold) == pytest.approx(0.5)
    assert RetrievalStageEvaluator.compute_mrr(["d2", "d1"], gold) == 1.0


def test_mrr_no_relevant_returns_zero():
    assert RetrievalStageEvaluator.compute_mrr(["d9", "d8"], {"d1"}) == 0.0
    assert RetrievalStageEvaluator.compute_mrr([], {"d1"}) == 0.0


# --------------------------------------------------------------------------- #
# Single-stage evaluation
# --------------------------------------------------------------------------- #
def test_evaluate_stage_single_query_metrics():
    evaluator = RetrievalStageEvaluator(k_values=[1, 5])
    results = [_result("d1", 0.9), _result("d2", 0.8), _result("d3", 0.7)]
    gold = {"d1", "d3"}
    sm = evaluator.evaluate_stage(results, gold, [1, 5])
    assert isinstance(sm, StageMetrics)
    # precision@1 = 1/1 = 1.0 (d1 is relevant)
    assert sm.precision_at_k[1] == 1.0
    # recall@5 = 2/2 = 1.0
    assert sm.recall_at_k[5] == 1.0
    # mrr = 1/1 = 1.0
    assert sm.mrr == 1.0
    # ndcg@5: relevant at ranks 1 and 3.
    dcg = 1.0 / math.log2(2) + 1.0 / math.log2(4)
    idcg = 1.0 / math.log2(2) + 1.0 / math.log2(3)
    assert sm.ndcg_at_k[5] == pytest.approx(dcg / idcg)


def test_evaluate_stage_empty_results():
    evaluator = RetrievalStageEvaluator(k_values=[1, 5, 10])
    sm = evaluator.evaluate_stage([], {"d1", "d2"}, [1, 5, 10])
    assert all(v == 0.0 for v in sm.precision_at_k.values())
    assert all(v == 0.0 for v in sm.recall_at_k.values())
    assert all(v == 0.0 for v in sm.ndcg_at_k.values())
    assert sm.mrr == 0.0


def test_evaluate_stage_rank_ordering_respected():
    """Results carrying an explicit `rank` are ordered by rank, not list order."""
    evaluator = RetrievalStageEvaluator(k_values=[1, 2])
    # List order is scrambled but rank says d2 is first.
    results = [_ranked("d1", 2), _ranked("d2", 1)]
    gold = {"d2"}
    sm = evaluator.evaluate_stage(results, gold, [1, 2])
    assert sm.precision_at_k[1] == 1.0  # d2 is the top hit
    assert sm.mrr == 1.0


# --------------------------------------------------------------------------- #
# Multi-stage pipeline evaluation
# --------------------------------------------------------------------------- #
def _build_three_stage_pipeline():
    """dense (weak) -> fusion (better) -> rerank (best), across two queries.

    Each stage genuinely improves NDCG over the previous one:
    - dense: top hit is *irrelevant*, one gold doc appears at rank 2.
    - fusion: both gold docs found, but the second gold doc sits at rank 3.
    - rerank: both gold docs at ranks 1-2 (perfect ordering).

    Binary-relevance NDCG is order-insensitive once all gold docs are within
    top-k, so the improvement must come from *promoting a gold doc into a
    better rank*, not just reordering two already-present gold docs.
    """
    stage_results = {
        "dense": [
            # q1: d4 (noise) first, d3 (gold) at rank 2, d1 missing
            _result("d4", 0.9, "q1"), _result("d3", 0.5, "q1"),
            # q2: d5 (noise) first, d2 (gold) at rank 2, d1 missing
            _result("d5", 0.9, "q2"), _result("d2", 0.5, "q2"),
        ],
        "fusion": [
            # q1: d3 (gold) at rank 1, d1 (gold) at rank 3
            _result("d3", 0.95, "q1"), _result("d4", 0.6, "q1"), _result("d1", 0.5, "q1"),
            # q2: d2 (gold) at rank 1, d1 (gold) at rank 3
            _result("d2", 0.95, "q2"), _result("d5", 0.6, "q2"), _result("d1", 0.5, "q2"),
        ],
        "rerank": [
            # q1: d1, d3 both gold at ranks 1-2 (perfect)
            _result("d1", 0.99, "q1"), _result("d3", 0.9, "q1"),
            # q2: d1, d2 both gold at ranks 1-2 (perfect)
            _result("d1", 0.99, "q2"), _result("d2", 0.9, "q2"),
        ],
    }
    ground_truth = {
        "q1": {"d1", "d3"},
        "q2": {"d1", "d2"},
    }
    return stage_results, ground_truth


def test_evaluate_pipeline_report_shape_and_stage_names():
    evaluator = RetrievalStageEvaluator(k_values=[1, 5, 10])
    stage_results, ground_truth = _build_three_stage_pipeline()
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    assert isinstance(report, StageContributionReport)
    assert report.total_queries == 2
    assert [sm.stage_name for sm in report.stage_metrics] == ["dense", "fusion", "rerank"]
    # Every stage has entries for all k values.
    for sm in report.stage_metrics:
        assert set(sm.precision_at_k) == {1, 5, 10}
    for sm in report.stage_metrics:
        assert set(sm.recall_at_k) == {1, 5, 10}
        assert set(sm.ndcg_at_k) == {1, 5, 10}

def test_evaluate_pipeline_aggregation_is_mean_over_queries():
    evaluator = RetrievalStageEvaluator(k_values=[1])
    stage_results, ground_truth = _build_three_stage_pipeline()
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    # dense@1: q1 top hit d4 (irrelevant) -> 0.0; q2 top hit d5 (irrelevant) -> 0.0; mean 0.0
    assert report.stage_metrics[0].precision_at_k[1] == pytest.approx(0.0)
    # rerank@1: q1 top hit d1 (relevant) -> 1.0; q2 top hit d1 (relevant) -> 1.0; mean 1.0
    assert report.stage_metrics[2].precision_at_k[1] == pytest.approx(1.0)
    # recall@1 for dense: q1 0/2, q2 0/2 -> mean 0.0 (top hit is noise)
    assert report.stage_metrics[0].recall_at_k[1] == pytest.approx(0.0)
    # recall@1 for rerank: q1 1/2, q2 1/2 -> mean 0.5 (only top-1 counted)
    assert report.stage_metrics[2].recall_at_k[1] == pytest.approx(0.5)


# --------------------------------------------------------------------------- #
# Marginal improvement
# --------------------------------------------------------------------------- #
def test_marginal_improvement_first_stage_equals_own_ndcg():
    evaluator = RetrievalStageEvaluator(k_values=[1, 5])
    stage_results, ground_truth = _build_three_stage_pipeline()
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    dense_ndcg = report.stage_metrics[0].ndcg_at_k
    for k in (1, 5):
        assert report.marginal_improvement["dense"][k] == pytest.approx(dense_ndcg[k])


def test_marginal_improvement_is_delta_over_previous_stage():
    evaluator = RetrievalStageEvaluator(k_values=[5])
    stage_results, ground_truth = _build_three_stage_pipeline()
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    dense = report.stage_metrics[0].ndcg_at_k[5]
    fusion = report.stage_metrics[1].ndcg_at_k[5]
    rerank = report.stage_metrics[2].ndcg_at_k[5]
    assert report.marginal_improvement["fusion"][5] == pytest.approx(fusion - dense)
    assert report.marginal_improvement["rerank"][5] == pytest.approx(rerank - fusion)
    # Adding stages improves NDCG here, so deltas are non-negative.
    assert report.marginal_improvement["fusion"][5] >= 0.0
    assert report.marginal_improvement["rerank"][5] >= 0.0


# --------------------------------------------------------------------------- #
# Diminishing returns
# --------------------------------------------------------------------------- #
def test_diminishing_returns_detected_for_tiny_gain():
    """A final stage that barely moves NDCG is flagged as diminishing."""
    evaluator = RetrievalStageEvaluator(k_values=[5], diminishing_threshold=0.1)
    stage_results = {
        "dense": [
            _result("d1", 0.9, "q1"), _result("d3", 0.8, "q1"),
        ],
        "rerank": [
            # Same effective ordering -> NDCG barely changes.
            _result("d1", 0.95, "q1"), _result("d3", 0.9, "q1"),
        ],
    }
    ground_truth = {"q1": {"d1", "d3"}}
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    assert "rerank" in report.diminishing_return_stages
    assert "dense" not in report.diminishing_return_stages


def test_no_diminishing_returns_when_every_stage_helps():
    evaluator = RetrievalStageEvaluator(k_values=[5], diminishing_threshold=0.01)
    stage_results, ground_truth = _build_three_stage_pipeline()
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    # Each stage meaningfully improves NDCG, so none are flagged.
    assert report.diminishing_return_stages == []


# --------------------------------------------------------------------------- #
# Best combination selection
# --------------------------------------------------------------------------- #
def test_best_stage_combination_is_highest_ndcg_prefix():
    evaluator = RetrievalStageEvaluator(k_values=[1, 5, 10])
    stage_results, ground_truth = _build_three_stage_pipeline()
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    # rerank is the strongest stage -> full chain is best.
    assert report.best_stage_combination == "dense+fusion+rerank"


def test_best_stage_combination_prefers_shorter_on_tie():
    """When a late stage adds nothing, the cheaper prefix wins."""
    evaluator = RetrievalStageEvaluator(k_values=[5], diminishing_threshold=0.01)
    stage_results = {
        "dense": [_result("d1", 0.9, "q1"), _result("d3", 0.8, "q1")],
        "rerank": [_result("d1", 0.99, "q1"), _result("d3", 0.9, "q1")],
    }
    ground_truth = {"q1": {"d1", "d3"}}
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    # Both stages produce the same ordering -> same NDCG -> shorter prefix wins.
    assert report.best_stage_combination == "dense"


# --------------------------------------------------------------------------- #
# Edge cases: empty / perfect / no relevant found / missing query
# --------------------------------------------------------------------------- #
def test_evaluate_pipeline_empty_stage_results():
    evaluator = RetrievalStageEvaluator(k_values=[1, 5])
    report = evaluator.evaluate_pipeline({}, {"q1": {"d1"}})
    assert report.total_queries == 1
    assert report.stage_metrics == []
    assert report.best_stage_combination == ""
    assert report.diminishing_return_stages == []


def test_evaluate_pipeline_perfect_retrieval():
    evaluator = RetrievalStageEvaluator(k_values=[1, 2, 5])
    stage_results = {
        "rerank": [
            _result("d1", 0.99, "q1"), _result("d2", 0.9, "q1"),
        ],
    }
    ground_truth = {"q1": {"d1", "d2"}}
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    sm = report.stage_metrics[0]
    assert sm.precision_at_k[2] == 1.0
    assert sm.recall_at_k[2] == 1.0
    assert sm.ndcg_at_k[2] == pytest.approx(1.0)
    assert sm.mrr == 1.0
    assert report.best_stage_combination == "rerank"


def test_evaluate_pipeline_no_relevant_docs_found():
    """When no stage retrieves any gold doc, every metric is zero."""
    evaluator = RetrievalStageEvaluator(k_values=[1, 5])
    stage_results = {
        "dense": [_result("d9", 0.9, "q1"), _result("d8", 0.5, "q1")],
        "rerank": [_result("d9", 0.99, "q1"), _result("d8", 0.9, "q1")],
    }
    ground_truth = {"q1": {"d1", "d2"}}
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    for sm in report.stage_metrics:
        assert all(v == 0.0 for v in sm.precision_at_k.values())
        assert all(v == 0.0 for v in sm.recall_at_k.values())
        assert all(v == 0.0 for v in sm.ndcg_at_k.values())
        assert sm.mrr == 0.0
    # Marginal improvement is zero everywhere; rerank is below threshold.
    assert report.marginal_improvement["rerank"][5] == 0.0
    assert "rerank" in report.diminishing_return_stages


def test_evaluate_pipeline_missing_query_results_score_zero():
    """A query with no results for a stage scores zero for that stage, not an error."""
    evaluator = RetrievalStageEvaluator(k_values=[1, 5])
    stage_results = {
        "dense": [
            # Only q1 has dense results; q2 has none.
            _result("d1", 0.9, "q1"),
        ],
    }
    ground_truth = {"q1": {"d1"}, "q2": {"d2"}}
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    assert report.total_queries == 2
    sm = report.stage_metrics[0]
    # q1 precision@1 = 1.0, q2 precision@1 = 0.0 -> mean 0.5
    assert sm.precision_at_k[1] == pytest.approx(0.5)
    # recall@1: q1 1/1, q2 0/1 -> mean 0.5
    assert sm.recall_at_k[1] == pytest.approx(0.5)


def test_per_query_analysis_structure():
    evaluator = RetrievalStageEvaluator(k_values=[1, 5])
    stage_results, ground_truth = _build_three_stage_pipeline()
    report = evaluator.evaluate_pipeline(stage_results, ground_truth)
    assert len(report.per_query_analysis) == 2
    qids = {entry["query_id"] for entry in report.per_query_analysis}
    assert qids == {"q1", "q2"}
    entry = report.per_query_analysis[0]
    assert set(entry["stage_metrics"]) == {"dense", "fusion", "rerank"}
    assert entry["best_stage"] in {"dense", "fusion", "rerank"}
    assert set(entry["marginal_improvement"]) == {"dense", "fusion", "rerank"}


# --------------------------------------------------------------------------- #
# Constructor validation
# --------------------------------------------------------------------------- #
def test_constructor_rejects_non_positive_k():
    with pytest.raises(ValueError):
        RetrievalStageEvaluator(k_values=[0, 5])


def test_constructor_default_k_values():
    evaluator = RetrievalStageEvaluator()
    assert evaluator.k_values == [1, 5, 10, 20]
    assert evaluator.diminishing_threshold == 0.01


def test_constructor_dedupes_and_sorts_k_values():
    evaluator = RetrievalStageEvaluator(k_values=[10, 1, 5, 1, 20])
    assert evaluator.k_values == [1, 5, 10, 20]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
