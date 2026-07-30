#!/usr/bin/env python3
"""Linux-isolated ANNOY measurement used when the host ARM wheel is broken."""

import json
import os
import statistics
import sys
import tempfile
import time

import numpy as np
from annoy import AnnoyIndex


def latency_stats(values):
    return {
        "mean": statistics.mean(values),
        "p50": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
    }


def main():
    input_path, output_path = sys.argv[1:3]
    data = np.load(input_path, allow_pickle=False)
    ids = [str(x) for x in data["ids"]]
    vectors = data["vectors"].astype("float32")
    queries = data["queries"].astype("float32")
    initial_truth = data["initial_truth"]
    full_truth = data["full_truth"]
    initial_n, k, repeats = (int(x) for x in data["parameters"])
    dimension = vectors.shape[1]

    index = AnnoyIndex(dimension, "angular")
    started = time.perf_counter()
    for i, vector in enumerate(vectors[:initial_n]):
        index.add_item(i, vector.tolist())
    index.build(50)
    build_ms = (time.perf_counter() - started) * 1000

    recalls, latencies, rankings = [], [], []
    for q_idx, query in enumerate(queries):
        first = None
        for _ in range(repeats):
            started = time.perf_counter()
            found = index.get_nns_by_vector(query.tolist(), k, -1, False)
            latencies.append((time.perf_counter() - started) * 1000)
            if first is None:
                first = found
        recalls.append(len(set(first) & set(initial_truth[q_idx].tolist())) / k)
        rankings.append({"query_index": q_idx, "doc_ids": [ids[i] for i in first]})

    with tempfile.NamedTemporaryFile() as handle:
        index.save(handle.name)
        serialized_bytes = os.path.getsize(handle.name)

    # ANNOY cannot mutate a built index: full update means rebuilding a fresh tree.
    started = time.perf_counter()
    updated = AnnoyIndex(dimension, "angular")
    for i, vector in enumerate(vectors):
        updated.add_item(i, vector.tolist())
    updated.build(50)
    update_ms = (time.perf_counter() - started) * 1000
    update_recalls = []
    for q_idx, query in enumerate(queries):
        found = updated.get_nns_by_vector(query.tolist(), k, -1, False)
        update_recalls.append(len(set(found) & set(full_truth[q_idx].tolist())) / k)

    payload = {
        "build_ms": round(build_ms, 3),
        "recall_at_k": statistics.mean(recalls),
        "query_latency_ms": latency_stats(latencies),
        "serialized_bytes": serialized_bytes,
        "rankings": rankings,
        "incremental_update": {
            "items_added": len(ids) - initial_n,
            "latency_ms": round(update_ms, 3),
            "requires_full_rebuild": True,
            "recall_at_k_after_update": statistics.mean(update_recalls),
        },
    }
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


if __name__ == "__main__":
    main()
