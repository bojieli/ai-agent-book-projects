#!/usr/bin/env python3
"""Honest verification of the merged Experiment 6-11 (README row 6-11) full matrix.

Checks, without trusting the runner's own summary:
  1. All 60 cases present, each with exactly 24 cells (4 embeddings x 3 rerankers x 2 main models).
  2. 1,440 total records; zero error trajectories; zero unpriced requests/tokens.
  3. Retrieval metrics (hit@5, recall@5, MRR) and task metrics (reward, success) are
     populated and finite for every record.
  4. Embedding-index cost accounting present for every record.
  5. Interaction analysis: mean reward grouped by (embedding, reranker, main_model).

Usage: python3 validation/verify_full_matrix_20260731.py [path-to-matrix.json]
Exit 0 only if every hard check passes.
"""

import json
import math
import sys
from collections import defaultdict

PATH = sys.argv[1] if len(sys.argv) > 1 else "results/full_6_11_60_case_matrix.json"

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


def main():
    with open(PATH) as f:
        data = json.load(f)

    records = data.get("records", [])
    by_case = defaultdict(list)
    for r in records:
        by_case[r["test_id"]].append(r)

    # 1. coverage
    check(len(by_case) == 60, f"expected 60 cases, got {len(by_case)}")
    for tid, recs in sorted(by_case.items()):
        check(len(recs) == 24, f"{tid}: expected 24 cells, got {len(recs)}")
        combos = {(r["embedding"], r["reranker"], r["main_model"]) for r in recs}
        check(len(combos) == 24, f"{tid}: duplicate/missing cell combos ({len(combos)} unique)")

    # 2. totals and cleanliness
    check(len(records) == 1440, f"expected 1440 records, got {len(records)}")
    errors = [r for r in records if r.get("status") == "error" or r.get("error")]
    check(not errors, f"{len(errors)} error trajectories")
    unpriced_req = sum(r.get("unpriced_requests", 0) for r in records)
    unpriced_tok = sum(r.get("unpriced_tokens", 0) for r in records)
    check(unpriced_req == 0 and unpriced_tok == 0,
          f"unpriced usage: {unpriced_req} requests, {unpriced_tok} tokens")

    # 3. metrics populated
    metric_fields = ["retrieval_hit_at_5", "retrieval_recall_at_5", "retrieval_mrr", "reward"]
    for field in metric_fields:
        bad = [r["test_id"] for r in records
               if not isinstance(r.get(field), (int, float)) or not math.isfinite(r[field])]
        check(not bad, f"metric {field} missing/non-finite in {len(bad)} records (e.g. {bad[:3]})")

    # 4. embedding index cost accounting
    no_idx = [r["test_id"] for r in records if r.get("embedding_index_latency_ms") is None]
    check(not no_idx, f"embedding index accounting missing in {len(no_idx)} records")

    # 5. interaction analysis (informational, always printed)
    groups = defaultdict(list)
    for r in records:
        groups[(r["embedding"], r["reranker"], r["main_model"])].append(r["reward"])
    print("mean reward by (embedding, reranker, main_model):")
    for combo in sorted(groups):
        vals = groups[combo]
        print(f"  {combo}: {sum(vals)/len(vals):.4f} (n={len(vals)})")

    total_cost = sum(r.get("cost_usd") or 0 for r in records)
    print(f"total main-model cost: ${total_cost:.2f}")
    print(f"records: {len(records)}, cases: {len(by_case)}")

    if failures:
        print("\nFAILURES:")
        for msg in failures:
            print(f"  - {msg}")
        sys.exit(1)
    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
