#!/usr/bin/env python3
"""Canonical real-model campaign for Chapter 3 Experiment 3-6."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
CHAPTER_DIR = PROJECT_DIR.parent
sys.path.insert(0, str(CHAPTER_DIR))

from experiment_utils import write_campaign_evidence  # noqa: E402
from evaluate import (  # noqa: E402
    DEFAULT_CORPUS,
    DEFAULT_QUERIES,
    METHOD_LABELS,
    Pipeline,
    build_parser,
    run_evaluation,
)


def cached_revision(model_name: str) -> str | None:
    ref = Path.home() / ".cache" / "huggingface" / "hub" / (
        "models--" + model_name.replace("/", "--")
    ) / "refs" / "main"
    return ref.read_text(encoding="utf-8").strip() if ref.exists() else None


def model_identity(pipeline: Pipeline, embed_name: str, reranker_name: str) -> dict:
    encoder = pipeline.dense.encoder
    reranker = pipeline.reranker
    return {
        "dense": {
            "provider": "local Hugging Face transformers",
            "model": embed_name,
            "cached_revision": cached_revision(embed_name),
            "class": type(encoder.model).__name__,
            "pooling": encoder.pooling,
            "parameters": sum(p.numel() for p in encoder.model.parameters()),
            "device": encoder.device,
        },
        "reranker": {
            "provider": "local Hugging Face transformers",
            "model": reranker_name,
            "cached_revision": cached_revision(reranker_name),
            "class": type(reranker.model).__name__,
            "parameters": sum(p.numel() for p in reranker.model.parameters()),
            "device": reranker.device,
        },
        "sparse": {"implementation": "rank_bm25.BM25Okapi"},
    }


def main() -> int:
    args = build_parser().parse_args([])
    args.embed_model = "Qwen/Qwen3-Embedding-0.6B"
    args.reranker_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    args.pooling = "auto"
    args.device = "cpu"
    args.top_k = 10
    args.eval_k = 3
    args.rerank_pool = 10
    args.rerank_top_k = 10
    args.use_dense = True
    args.use_rerank = True

    pipeline = Pipeline(DEFAULT_CORPUS, args)
    report = run_evaluation(pipeline, DEFAULT_QUERIES, args)
    identities = model_identity(pipeline, args.embed_model, args.reranker_model)
    methods = {key for key, _ in METHOD_LABELS}
    observed_methods = set(report["summary"])
    categories = {query.get("category") for query in DEFAULT_QUERIES}
    expected_categories = {"semantic", "exact-name", "multilingual", "technical-code"}
    all_rank_changes = [
        {"query": row["query"], **change}
        for row in report["per_query"]
        for change in row["trace"]["rank_changes"]
    ]
    acceptance = {
        "real_dense_model_loaded": identities["dense"]["parameters"] > 100_000_000,
        "real_cross_encoder_loaded": identities["reranker"]["parameters"] > 1_000_000,
        "identical_labelled_queries_for_all_methods": all(
            set(row["methods"]) == methods for row in report["per_query"]
        ),
        "all_required_query_categories_present": expected_categories <= categories,
        "sparse_dense_rrf_weighted_reranked_measured": observed_methods == methods,
        "recall_mrr_ndcg_and_latency_measured": all(
            {"recall@k", "mrr", "ndcg@k", "latency_ms"} <= set(metrics)
            for metrics in report["summary"].values()
        ),
        "rank_changes_retained": bool(all_rank_changes),
        "hybrid_recall_not_below_best_single": report["summary"]["rrf"]["recall@k"]
        >= max(report["summary"]["sparse"]["recall@k"], report["summary"]["dense"]["recall@k"]),
    }
    evidence = {
        "status": "passed" if all(acceptance.values()) else "failed",
        "models": identities,
        "configuration": {
            "documents": len(DEFAULT_CORPUS),
            "chunks": pipeline.n_chunks,
            "queries": len(DEFAULT_QUERIES),
            "top_k": args.top_k,
            "eval_k": args.eval_k,
            "rrf_k": args.k_rrf,
            "rerank_pool": args.rerank_pool,
            "device": args.device,
        },
        "dataset": {"corpus": DEFAULT_CORPUS, "queries": DEFAULT_QUERIES},
        "report": report,
        "rank_changes": all_rank_changes,
        "summary": report["summary"],
        "acceptance": acceptance,
    }
    manifest = write_campaign_evidence(
        PROJECT_DIR,
        "3-6",
        evidence,
        receipts=[
            {
                "kind": "local-model-execution",
                "models": identities,
                "note": "No remote API or credential was used; complete rankings and timings are in evidence.json.",
            }
        ],
        input_paths=[__file__, PROJECT_DIR / "evaluate.py", PROJECT_DIR / "fusion.py"],
    )
    print(json.dumps(report["summary"], indent=2))
    print(f"evidence: {manifest['run_dir']}")
    return 0 if all(acceptance.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
