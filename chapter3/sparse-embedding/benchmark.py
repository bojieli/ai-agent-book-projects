#!/usr/bin/env python3
"""Acceptance campaign for Chapter 3 Experiments 3-5.

This intentionally exercises the repository's from-scratch inverted index and
BM25 implementation.  It checks one score against an independent, explicit
calculation and then measures the exact-keyword/synonym contrast on a labelled
corpus.  No third-party retrieval implementation is used as an oracle.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
CHAPTER_DIR = PROJECT_DIR.parent
sys.path.insert(0, str(CHAPTER_DIR))

from experiment_utils import write_campaign_evidence  # noqa: E402
from bm25_engine import BM25, InvertedIndex, TextProcessor  # noqa: E402
from cli import DEFAULT_CORPUS, DEFAULT_LABELS, build_engine  # noqa: E402


K1 = 1.5
B = 0.75
TOP_K = 5


def hand_calculation() -> dict[str, Any]:
    """Compare engine output with a hand-calculable RSJ BM25 example."""

    texts = [
        "rare rare common",
        "common common",
        "common filler filler filler",
        "filler",
    ]
    index = InvertedIndex()
    for doc_id, text in enumerate(texts):
        index.add_document(doc_id, text, {"source": "hand-check"})
    bm25 = BM25(index, k1=K1, b=B)

    term = "rare"
    doc_id = 0
    n_docs = len(texts)
    df = 1
    tf = 2
    dl = 3
    avgdl = sum(len(TextProcessor().tokenize(text)) for text in texts) / n_docs
    idf = math.log((n_docs - df + 0.5) / (df + 0.5))
    numerator = tf * (K1 + 1)
    denominator = tf + K1 * (1 - B + B * (dl / avgdl))
    expected = idf * numerator / denominator
    raw_engine_idf = bm25.calculate_raw_idf(term)
    actual = bm25.calculate_term_score(term, doc_id)
    tolerance = 1e-12

    return {
        "corpus": texts,
        "term": term,
        "doc_id": doc_id,
        "parameters": {"N": n_docs, "df": df, "tf": tf, "dl": dl, "avgdl": avgdl, "k1": K1, "b": B},
        "formula": "ln((N-df+0.5)/(df+0.5)) * tf*(k1+1) / (tf+k1*(1-b+b*dl/avgdl))",
        "intermediate": {
            "independent_raw_idf": idf,
            "engine_raw_idf": raw_engine_idf,
            "scoring_idf": bm25.calculate_idf(term),
            "numerator": numerator,
            "denominator": denominator,
        },
        "expected_score": expected,
        "engine_score": actual,
        "absolute_error": abs(expected - actual),
        "tolerance": tolerance,
        "posting_list": sorted(index.get_posting_list(term)),
        "recorded_document_frequency": index.document_frequency[term],
        "passed": (
            abs(idf - raw_engine_idf) <= tolerance
            and abs(expected - actual) <= tolerance
            and index.document_frequency[term] == df
        ),
    }


def labelled_benchmark() -> dict[str, Any]:
    started = time.perf_counter()
    engine = build_engine(DEFAULT_CORPUS, k1=K1, b=B)
    build_ms = (time.perf_counter() - started) * 1000
    rows: list[dict[str, Any]] = []

    for query, relevant_list in DEFAULT_LABELS.items():
        query_start = time.perf_counter()
        results = engine.search(query, top_k=TOP_K)
        latency_ms = (time.perf_counter() - query_start) * 1000
        retrieved = [result["doc_id"] for result in results]
        relevant = set(relevant_list)
        hits = [doc_id for doc_id in retrieved if doc_id in relevant]
        recall = len(set(hits)) / len(relevant)
        reciprocal_rank = next(
            (1.0 / rank for rank, doc_id in enumerate(retrieved, 1) if doc_id in relevant),
            0.0,
        )
        category = "synonym-only" if query == "cat" else "exact-keyword"
        rows.append(
            {
                "query": query,
                "category": category,
                "relevant": sorted(relevant),
                "retrieved": retrieved,
                "hits": hits,
                "recall_at_5": recall,
                "reciprocal_rank": reciprocal_rank,
                "latency_ms": round(latency_ms, 3),
                "results": [
                    {
                        "rank": rank,
                        "doc_id": result["doc_id"],
                        "score": result["score"],
                        "matched_terms": result["debug"]["matched_terms"],
                        "term_frequencies": result["debug"]["term_frequencies"],
                    }
                    for rank, result in enumerate(results, 1)
                ],
            }
        )

    exact = [row for row in rows if row["category"] == "exact-keyword"]
    synonym = [row for row in rows if row["category"] == "synonym-only"]
    return {
        "corpus": DEFAULT_CORPUS,
        "labels": DEFAULT_LABELS,
        "parameters": {"k1": K1, "b": B, "top_k": TOP_K},
        "index_statistics": engine.index.get_statistics(),
        "build_latency_ms": round(build_ms, 3),
        "queries": rows,
        "metrics": {
            "exact_keyword_recall_at_5": sum(row["recall_at_5"] for row in exact) / len(exact),
            "exact_keyword_mrr": sum(row["reciprocal_rank"] for row in exact) / len(exact),
            "synonym_only_recall_at_5": sum(row["recall_at_5"] for row in synonym) / len(synonym),
            "synonym_only_mrr": sum(row["reciprocal_rank"] for row in synonym) / len(synonym),
        },
    }


def main() -> int:
    hand = hand_calculation()
    benchmark = labelled_benchmark()
    metrics = benchmark["metrics"]
    acceptance = {
        "uses_from_scratch_engine": True,
        "hand_score_matches": hand["passed"],
        "inverted_index_df_matches": hand["recorded_document_frequency"] == hand["parameters"]["df"],
        "all_exact_keyword_queries_recalled": metrics["exact_keyword_recall_at_5"] == 1.0,
        "synonym_only_failure_observed": metrics["synonym_only_recall_at_5"] == 0.0,
        "transparent_tf_idf_scores_retained": all(
            "term_frequencies" in result
            for row in benchmark["queries"]
            for result in row["results"]
        ),
    }
    passed = all(acceptance.values())
    evidence = {
        "status": "passed" if passed else "failed",
        "method": {
            "implementation": "chapter3/sparse-embedding/bm25_engine.py",
            "algorithm": "from-scratch inverted index + Robertson/Sparck Jones BM25",
            "third_party_retrieval_library": None,
        },
        "hand_calculation": hand,
        "benchmark": benchmark,
        "summary": metrics,
        "acceptance": acceptance,
    }
    manifest = write_campaign_evidence(
        PROJECT_DIR,
        "3-5",
        evidence,
        input_paths=[__file__, PROJECT_DIR / "bm25_engine.py", PROJECT_DIR / "cli.py"],
    )
    print(f"hand score error: {hand['absolute_error']:.3g}")
    print(f"exact recall@5: {metrics['exact_keyword_recall_at_5']:.3f}")
    print(f"synonym recall@5: {metrics['synonym_only_recall_at_5']:.3f}")
    print(f"evidence: {manifest['run_dir']}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
