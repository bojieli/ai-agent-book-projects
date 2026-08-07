"""Result fusion for hybrid retrieval.

This module implements the *fusion* stage of the hybrid retrieval pipeline —
the step that merges the separately-ranked dense and sparse candidate lists into
a single, unified candidate pool before neural reranking.

Two production-grade fusion strategies are provided, matching the two approaches
discussed in the book (第3章「混合检索流水线」):

1. Reciprocal Rank Fusion (RRF)
   score(d) = Σ_r  1 / (k + rank_r(d))
   Only ranks are used, original scores are discarded. Robust and scale-free,
   because it never has to compare a cosine similarity against a BM25 score.

2. Weighted score fusion (min-max normalized)
   score(d) = Σ_r  w_r * normalize_r(score_r(d))
   Keeps the original relevance signal, at the cost of having to align the two
   score scales via per-list min-max normalization.

Both functions take ranked lists of ``(doc_id, score)`` tuples (sorted by score
descending) and return a fused list of ``(doc_id, fused_score)`` tuples, also
sorted descending. A document that appears in only one list is still fused —
its contribution from the missing list is simply zero.
"""

from typing import Dict, List, Optional, Sequence, Tuple

RankedList = Sequence[Tuple[str, float]]

# Default smoothing constant for RRF. k=60 is the value from the original
# Cormack et al. paper and the most common choice in practice; it compresses the
# score gap between the very top ranks.
DEFAULT_RRF_K = 60


def _ranked_to_score_map(ranked: RankedList) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for doc_id, score in ranked:
        if doc_id not in scores:
            scores[doc_id] = score
    return scores
def min_max_normalize(scores: Dict[str, float]) -> Dict[str, float]:
    """Min-max normalize a mapping of doc_id -> score into the [0, 1] range.

    Args:
        scores: Mapping from document id to raw score.

    Returns:
        Mapping from document id to normalized score. If every score is equal
        (or there is a single document), all documents receive 1.0.
    """
    if not scores:
        return {}

    values = list(scores.values())
    lo, hi = min(values), max(values)
    span = hi - lo

    if span <= 0:
        # Degenerate case: all scores identical -> treat as equally relevant.
        return {doc_id: 1.0 for doc_id in scores}

    return {doc_id: (score - lo) / span for doc_id, score in scores.items()}


def reciprocal_rank_fusion(
    ranked_lists: Dict[str, RankedList],
    k: int = DEFAULT_RRF_K,
    weights: Optional[Dict[str, float]] = None,
) -> List[Tuple[str, float]]:
    """Fuse multiple ranked lists with Reciprocal Rank Fusion (RRF).

    Args:
        ranked_lists: Mapping from source name (e.g. "dense", "sparse") to a
            list of ``(doc_id, score)`` tuples sorted by score descending. Only
            the *order* of each list matters; the scores are ignored.
        k: RRF smoothing constant (default 60).
        weights: Optional per-source weights. Defaults to 1.0 for every source.

    Returns:
        Fused list of ``(doc_id, fused_score)`` tuples sorted descending.
    """
    weights = weights or {}
    fused: Dict[str, float] = {}

    for source, ranked in ranked_lists.items():
        weight = weights.get(source, 1.0)
        for rank, (doc_id, _score) in enumerate(ranked, start=1):
            fused[doc_id] = fused.get(doc_id, 0.0) + weight * (1.0 / (k + rank))

    return sorted(fused.items(), key=lambda kv: kv[1], reverse=True)


def weighted_score_fusion(
    ranked_lists: Dict[str, RankedList],
    weights: Optional[Dict[str, float]] = None,
) -> List[Tuple[str, float]]:
    """Fuse multiple ranked lists with weighted, min-max normalized scores.

    Each source list is min-max normalized to [0, 1] independently, then the
    normalized scores are combined with a weighted sum. A document missing from
    a source contributes 0 for that source.

    Args:
        ranked_lists: Mapping from source name to ``(doc_id, score)`` tuples.
        weights: Optional per-source weights. Defaults to 1.0 for every source.

    Returns:
        Fused list of ``(doc_id, fused_score)`` tuples sorted descending.
    """
    weights = weights or {}
    normalized_by_source = {
        source: min_max_normalize(_ranked_to_score_map(ranked))
        for source, ranked in ranked_lists.items()
    }

    fused: Dict[str, float] = {}
    for source, normalized in normalized_by_source.items():
        weight = weights.get(source, 1.0)
        for doc_id, norm_score in normalized.items():
            fused[doc_id] = fused.get(doc_id, 0.0) + weight * norm_score

    return sorted(fused.items(), key=lambda kv: kv[1], reverse=True)


def fuse(
    ranked_lists: Dict[str, RankedList],
    method: str = "rrf",
    k: int = DEFAULT_RRF_K,
    weights: Optional[Dict[str, float]] = None,
) -> List[Tuple[str, float]]:
    """Dispatch helper: fuse ranked lists with the named method.

    Args:
        ranked_lists: Mapping from source name to ``(doc_id, score)`` tuples.
        method: "rrf" for Reciprocal Rank Fusion, "weighted" for weighted
            min-max normalized score fusion.
        k: RRF smoothing constant (only used when method="rrf").
        weights: Optional per-source weights.

    Returns:
        Fused list of ``(doc_id, fused_score)`` tuples sorted descending.

    Raises:
        ValueError: If ``method`` is not recognized.
    """
    if method == "rrf":
        return reciprocal_rank_fusion(ranked_lists, k=k, weights=weights)
    if method == "weighted":
        return weighted_score_fusion(ranked_lists, weights=weights)
    raise ValueError(f"Unknown fusion method: {method!r} (expected 'rrf' or 'weighted')")
