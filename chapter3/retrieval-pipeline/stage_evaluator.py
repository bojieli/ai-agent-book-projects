"""Stage-level evaluation for the hybrid retrieval pipeline.

The book's 第3章「混合检索流水线」(experiment 3-6) chains four retrieval
stages — dense retrieval, sparse retrieval, fusion of the two, and neural
reranking — and judges the whole pipeline with aggregate metrics. What it does
not provide is an *automated, stage-level* evaluator that answers two questions
the experiment raises but leaves to the reader:

1. **Contribution**: how much does each stage actually add to final quality?
   (dense alone vs. dense+sparse vs. dense+sparse+rerank)
2. **Diminishing returns**: at what point does an extra stage stop paying for
   itself?

``RetrievalStageEvaluator`` takes a query set with ground-truth relevant
document IDs and pre-computed ranked results from each pipeline stage, computes
precision@k / recall@k / NDCG@k / MRR per stage, measures the marginal
improvement of adding each stage over the previous one, flags stages whose
marginal gain falls below a configurable threshold, and emits a
``StageContributionReport`` with both per-query and aggregate analysis.

The metric definitions match ``evaluate.py`` (binary relevance): NDCG uses a
``1 / log2(rank + 1)`` gain, MRR is ``1 / rank`` of the first relevant hit, and
recall is ``|topk ∩ gold| / |gold|``. Precision@k is the standard
``|topk ∩ gold| / k``. No network, no model, no GPU — the evaluator is a pure
function of the ranked lists and the gold sets it is handed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Sequence

__all__ = [
    "StageMetrics",
    "StageContributionReport",
    "RetrievalStageEvaluator",
]


# ---------------------------------------------------------------------------
# Result-shape helpers
# ---------------------------------------------------------------------------

# Keys tried, in priority order, when extracting a document id from a result
# dict. The pipeline's ``SearchResult`` / reranker output uses ``doc_id``; some
# fixtures use ``id``. Both are accepted so the evaluator is shape-tolerant.
_DOC_ID_KEYS = ("doc_id", "id", "_id", "document_id")


def _extract_doc_id(result: dict[str, Any]) -> str:
    """Pull the document id out of a single result dict."""
    for key in _DOC_ID_KEYS:
        value = result.get(key)
        if value is not None:
            return str(value)
    raise KeyError(
        "result dict has no document id under any of "
        f"{_DOC_ID_KEYS!r}; got keys {list(result)!r}"
    )


def _extract_ranked_ids(results: Sequence[dict[str, Any]]) -> list[str]:
    """Turn a list of result dicts into an ordered list of document ids.

    Ordering priority: an explicit ``rank`` field (ascending), then an explicit
    ``score`` field (descending), then the original list order. Deduplicates
    while preserving the first (best) occurrence — a doc should only be counted
    once even if a buggy stage emits it twice.
    """
    if not results:
        return []

    items: list[tuple[str, float]] = []
    has_rank = any("rank" in r for r in results)
    has_score = any("score" in r for r in results)

    for idx, result in enumerate(results):
        doc_id = _extract_doc_id(result)
        if has_rank:
            # rank is 1-indexed ascending; missing rank sorts last by index.
            sort_key = float(result.get("rank", idx))
        elif has_score:
            # score is descending; negate so larger score sorts first.
            sort_key = -float(result.get("score", 0.0))
        else:
            # Preserve insertion order with a stable key.
            sort_key = float(idx)
        items.append((doc_id, sort_key))

    items.sort(key=lambda kv: kv[1])

    seen: set[str] = set()
    ranked: list[str] = []
    for doc_id, _ in items:
        if doc_id in seen:
            continue
        seen.add(doc_id)
        ranked.append(doc_id)
    return ranked


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class StageMetrics:
    """Metrics for one stage, aggregated (mean) over the query set.

    ``precision_at_k`` / ``recall_at_k`` / ``ndcg_at_k`` map each evaluated k to
    its aggregate value; ``mrr`` is the mean reciprocal rank over all queries.
    """

    stage_name: str
    precision_at_k: dict[int, float] = field(default_factory=dict)
    recall_at_k: dict[int, float] = field(default_factory=dict)
    ndcg_at_k: dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0


@dataclass
class StageContributionReport:
    """Full stage-contribution analysis for a multi-stage retrieval pipeline."""

    total_queries: int
    stage_metrics: list[StageMetrics]
    # stage_name -> k -> improvement of that stage over the previous stage
    # (the first stage's "improvement" is measured over an empty baseline, so
    # its values equal its own NDCG@k).
    marginal_improvement: dict[str, dict[int, float]] = field(default_factory=dict)
    # Stages (after the first) whose mean marginal NDCG@k gain across all k is
    # below ``diminishing_threshold``.
    diminishing_return_stages: list[str] = field(default_factory=list)
    # Cumulative prefix (e.g. "dense+sparse+rerank") with the highest mean
    # NDCG@k across k; ties resolve to the shorter (cheaper) combination.
    best_stage_combination: str = ""
    # One entry per query with per-stage metrics and per-query marginal gains.
    per_query_analysis: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


class RetrievalStageEvaluator:
    """Measure how much each stage of a retrieval pipeline contributes.

    The evaluator is stage-agnostic: it works with any ordered set of stages
    whose results are supplied as ranked lists of result dicts. The stage order
    in ``stage_results`` defines the accumulation chain used for marginal
    improvement and best-combination selection (e.g. for the book's pipeline the
    caller passes ``{"dense": ..., "sparse": ..., "fusion": ..., "rerank": ...}``
    and the cumulative combinations become ``dense``, ``dense+sparse``,
    ``dense+sparse+fusion``, ``dense+sparse+fusion+rerank``).
    """

    def __init__(
        self,
        k_values: list[int] | None = None,
        diminishing_threshold: float = 0.01,
    ) -> None:
        self.k_values: list[int] = sorted(set(k_values or [1, 5, 10, 20]))
        if any(k < 1 for k in self.k_values):
            raise ValueError("k_values must be positive integers")
        self.diminishing_threshold = float(diminishing_threshold)

    # -- atomic metric primitives -------------------------------------------

    @staticmethod
    def compute_precision_at_k(
        ranked_ids: list[str], relevant_ids: set[str], k: int
    ) -> float:
        """Precision@k = |top-k ∩ relevant| / k (0.0 when k <= 0)."""
        if k <= 0:
            return 0.0
        topk = set(ranked_ids[:k])
        return len(topk & relevant_ids) / k

    @staticmethod
    def compute_recall_at_k(
        ranked_ids: list[str], relevant_ids: set[str], k: int
    ) -> float:
        """Recall@k = |top-k ∩ relevant| / |relevant| (0.0 when no gold)."""
        if not relevant_ids:
            return 0.0
        topk = set(ranked_ids[:k])
        return len(topk & relevant_ids) / len(relevant_ids)

    @staticmethod
    def compute_ndcg_at_k(
        ranked_ids: list[str], relevant_ids: set[str], k: int
    ) -> float:
        """NDCG@k with binary relevance (matches ``evaluate.ndcg_at_k``).

        Gain per relevant hit at rank ``i`` (1-indexed) is ``1 / log2(i + 1)``;
        the ideal DCG places the ``min(|gold|, k)`` relevant docs in the top
        positions. Returns 0.0 when there is no ideal ranking (no gold).
        """
        if k <= 0 or not relevant_ids:
            return 0.0
        dcg = 0.0
        for idx, doc_id in enumerate(ranked_ids[:k], start=1):
            if doc_id in relevant_ids:
                dcg += 1.0 / math.log2(idx + 1)
        ideal_hits = min(len(relevant_ids), k)
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
        return dcg / idcg if idcg > 0 else 0.0

    @staticmethod
    def compute_mrr(ranked_ids: list[str], relevant_ids: set[str]) -> float:
        """Mean reciprocal rank source: 1 / rank of first relevant hit, else 0.0."""
        for idx, doc_id in enumerate(ranked_ids, start=1):
            if doc_id in relevant_ids:
                return 1.0 / idx
        return 0.0

    # -- per-(query, stage) evaluation --------------------------------------

    def evaluate_stage(
        self,
        results: list[dict[str, Any]],
        relevant_ids: set[str],
        k_values: list[int],
    ) -> StageMetrics:
        """Evaluate one stage's results for a single query.

        ``results`` is the ranked result-dict list for one (query, stage) pair;
        ``relevant_ids`` is that query's gold set. Returns a ``StageMetrics``
        with the per-k metrics and MRR for this single query. The
        ``stage_name`` is left blank here — ``evaluate_pipeline`` sets the real
        name when it aggregates across queries.
        """
        ranked_ids = _extract_ranked_ids(results)
        precision: dict[int, float] = {}
        recall: dict[int, float] = {}
        ndcg: dict[int, float] = {}
        for k in k_values:
            precision[k] = self.compute_precision_at_k(ranked_ids, relevant_ids, k)
            recall[k] = self.compute_recall_at_k(ranked_ids, relevant_ids, k)
            ndcg[k] = self.compute_ndcg_at_k(ranked_ids, relevant_ids, k)
        mrr = self.compute_mrr(ranked_ids, relevant_ids)
        return StageMetrics(
            stage_name="",
            precision_at_k=precision,
            recall_at_k=recall,
            ndcg_at_k=ndcg,
            mrr=mrr,
        )

    # -- whole-pipeline evaluation ------------------------------------------

    def evaluate_pipeline(
        self,
        stage_results: dict[str, list[dict[str, Any]]],
        ground_truth: dict[str, set[str]],
    ) -> StageContributionReport:
        """Evaluate every stage across the query set and build the report.

        ``stage_results`` maps stage name -> flat list of result dicts for that
        stage across *all* queries; each result dict must carry a ``query_id``
        (so it can be grouped back to its query) and a document id. Insertion
        order of ``stage_results`` defines the accumulation chain.

        ``ground_truth`` maps query id -> set of relevant document ids. The
        query set is exactly ``ground_truth.keys()``; queries appearing only in
        stage results are ignored, and queries with no results for a stage score
        zero for that stage.
        """
        stage_names = list(stage_results.keys())
        query_ids = list(ground_truth.keys())

        # Group each stage's flat result list by query_id, once.
        grouped: dict[str, dict[str, list[dict[str, Any]]]] = {
            stage: {} for stage in stage_names
        }
        for stage, results in stage_results.items():
            for result in results:
                qid = result.get("query_id")
                if qid is None:
                    raise KeyError(
                        f"stage {stage!r} result missing 'query_id'; "
                        f"got keys {list(result)!r}"
                    )
                grouped[stage].setdefault(qid, []).append(result)

        # Per-query, per-stage metrics.
        per_query_stage: dict[str, dict[str, StageMetrics]] = {
            qid: {} for qid in query_ids
        }
        for stage in stage_names:
            for qid in query_ids:
                relevant = ground_truth.get(qid, set())
                results = grouped[stage].get(qid, [])
                per_query_stage[qid][stage] = self.evaluate_stage(
                    results, relevant, self.k_values
                )

        # Aggregate each stage by mean over queries.
        stage_metrics: list[StageMetrics] = []
        for stage in stage_names:
            n = max(len(query_ids), 1)
            agg_precision: dict[int, float] = {
                k: sum(per_query_stage[qid][stage].precision_at_k[k] for qid in query_ids) / n
                for k in self.k_values
            }
            agg_recall: dict[int, float] = {
                k: sum(per_query_stage[qid][stage].recall_at_k[k] for qid in query_ids) / n
                for k in self.k_values
            }
            agg_ndcg: dict[int, float] = {
                k: sum(per_query_stage[qid][stage].ndcg_at_k[k] for qid in query_ids) / n
                for k in self.k_values
            }
            agg_mrr = sum(per_query_stage[qid][stage].mrr for qid in query_ids) / n
            stage_metrics.append(
                StageMetrics(
                    stage_name=stage,
                    precision_at_k=agg_precision,
                    recall_at_k=agg_recall,
                    ndcg_at_k=agg_ndcg,
                    mrr=agg_mrr,
                )
            )

        # Marginal improvement over the previous stage (NDCG@k as the
        # contribution signal). The first stage is measured against an empty
        # baseline, so its marginal equals its own NDCG@k.
        marginal_improvement: dict[str, dict[int, float]] = {}
        for i, stage in enumerate(stage_names):
            current = stage_metrics[i].ndcg_at_k
            if i == 0:
                marginal_improvement[stage] = {k: current[k] for k in self.k_values}
            else:
                previous = stage_metrics[i - 1].ndcg_at_k
                marginal_improvement[stage] = {
                    k: current[k] - previous[k] for k in self.k_values
                }

        # Diminishing returns: a non-first stage whose mean marginal NDCG@k
        # gain across all k is below the threshold.
        diminishing_return_stages: list[str] = []
        for i, stage in enumerate(stage_names):
            if i == 0:
                continue
            mean_gain = sum(marginal_improvement[stage].values()) / max(
                len(self.k_values), 1
            )
            if mean_gain < self.diminishing_threshold:
                diminishing_return_stages.append(stage)

        # Best cumulative combination: highest mean NDCG@k across k; ties go to
        # the shorter (cheaper) prefix.
        best_label = ""
        best_score = -1.0
        for i, stage in enumerate(stage_names):
            label = "+".join(stage_names[: i + 1])
            score = sum(stage_metrics[i].ndcg_at_k.values()) / max(
                len(self.k_values), 1
            )
            if score > best_score + 1e-12:
                best_score = score
                best_label = label
        if not stage_names:
            best_label = ""

        # Per-query analysis.
        per_query_analysis: list[dict[str, Any]] = []
        for qid in query_ids:
            stage_block: dict[str, dict[str, Any]] = {}
            for stage in stage_names:
                sm = per_query_stage[qid][stage]
                stage_block[stage] = {
                    "precision_at_k": dict(sm.precision_at_k),
                    "recall_at_k": dict(sm.recall_at_k),
                    "ndcg_at_k": dict(sm.ndcg_at_k),
                    "mrr": sm.mrr,
                }
            # Best stage for this query by mean NDCG@k (ties -> first stage).
            best_stage = ""
            best_q_score = -1.0
            for stage in stage_names:
                sm = per_query_stage[qid][stage]
                score = sum(sm.ndcg_at_k.values()) / max(len(self.k_values), 1)
                if score > best_q_score + 1e-12:
                    best_q_score = score
                    best_stage = stage
            # Per-query marginal improvement (NDCG@k).
            q_marginal: dict[str, dict[int, float]] = {}
            for i, stage in enumerate(stage_names):
                current = per_query_stage[qid][stage].ndcg_at_k
                if i == 0:
                    q_marginal[stage] = {k: current[k] for k in self.k_values}
                else:
                    previous = per_query_stage[qid][stage_names[i - 1]].ndcg_at_k
                    q_marginal[stage] = {
                        k: current[k] - previous[k] for k in self.k_values
                    }
            per_query_analysis.append(
                {
                    "query_id": qid,
                    "stage_metrics": stage_block,
                    "best_stage": best_stage,
                    "marginal_improvement": q_marginal,
                }
            )

        return StageContributionReport(
            total_queries=len(query_ids),
            stage_metrics=stage_metrics,
            marginal_improvement=marginal_improvement,
            diminishing_return_stages=diminishing_return_stages,
            best_stage_combination=best_label,
            per_query_analysis=per_query_analysis,
        )
