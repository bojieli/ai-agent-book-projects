#!/usr/bin/env python3
"""Real-embedding ANNOY vs HNSW benchmark for Experiment 3-4."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from experiment_utils import sha256_file, write_campaign_evidence

from indexing import AnnoyIndex, HNSWIndex


TOPICS = [
    ("vector search", "Approximate nearest-neighbor indexes accelerate semantic vector retrieval."),
    ("database transactions", "Database transactions use atomicity, consistency, isolation and durability."),
    ("photosynthesis", "Green plants turn sunlight and carbon dioxide into chemical energy."),
    ("quantum entanglement", "Entangled particles exhibit correlated quantum measurement outcomes."),
    ("contract law", "A valid contract generally requires offer acceptance and consideration."),
    ("neural networks", "Deep neural networks learn layered nonlinear representations from data."),
    ("cybersecurity", "Zero trust security continuously verifies identity and device posture."),
    ("volcanoes", "Volcanoes form when magma rises through fractures in the planetary crust."),
    ("water cycle", "Evaporation condensation precipitation and runoff form the water cycle."),
    ("operating systems", "An operating system schedules processes and manages memory and devices."),
    ("HTTP errors", "HTTP status 403 means a server understood but refused a request."),
    ("machine translation", "Multilingual models translate meaning between natural languages."),
    ("financial risk", "Portfolio diversification reduces exposure to idiosyncratic financial risk."),
    ("medical imaging", "Radiology systems analyze X-rays CT scans and magnetic resonance images."),
    ("supply chains", "Supply chain planning coordinates inventory logistics demand and suppliers."),
    ("climate science", "Climate models simulate long-term interactions among atmosphere ocean and land."),
    ("CPU instructions", "SIMD instructions apply one operation to several packed numeric values."),
    ("compiler design", "A compiler parses source code optimizes intermediate form and emits machine code."),
    ("graph theory", "Graph algorithms traverse vertices and edges to discover paths and communities."),
    ("astronomy", "Astronomers infer stellar properties from spectra luminosity and orbital motion."),
]


class TransformerEncoder:
    def __init__(self, model_name: str, device: str):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.model_name = model_name
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side="left")
        self.model = AutoModel.from_pretrained(model_name).to(device).eval()

    def encode(self, texts: Sequence[str], query: bool = False, batch_size: int = 16) -> np.ndarray:
        prefix = "Instruct: Retrieve semantically relevant passages.\nQuery:" if query else ""
        values = [prefix + text for text in texts]
        vectors = []
        for start in range(0, len(values), batch_size):
            batch = values[start : start + batch_size]
            tokens = self.tokenizer(
                batch, padding=True, truncation=True, max_length=192, return_tensors="pt"
            ).to(self.device)
            with self.torch.no_grad():
                output = self.model(**tokens).last_hidden_state[:, -1].float()
            output = self.torch.nn.functional.normalize(output, p=2, dim=1)
            vectors.append(output.cpu().numpy())
        return np.concatenate(vectors, axis=0).astype("float32")


def build_corpus(n_docs: int) -> tuple[List[str], List[str]]:
    docs, ids = [], []
    variants = (
        "A concise technical overview.",
        "This passage explains the central mechanism and its practical use.",
        "An engineering handbook entry with definitions and examples.",
        "A research summary intended for a multilingual knowledge base.",
        "Operational notes emphasizing trade-offs, reliability, and performance.",
    )
    for i in range(n_docs):
        topic, sentence = TOPICS[i % len(TOPICS)]
        variant = variants[(i // len(TOPICS)) % len(variants)]
        docs.append(f"Topic: {topic}. {sentence} {variant} Document revision {i:04d}.")
        ids.append(f"doc_{i:04d}")
    return ids, docs


def percentiles(values: List[float]) -> Dict[str, float]:
    return {
        "mean": statistics.mean(values),
        "p50": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
    }


def exact_neighbors(matrix: np.ndarray, queries: np.ndarray, k: int) -> List[List[int]]:
    scores = queries @ matrix.T
    return [np.argsort(-row)[:k].tolist() for row in scores]


def measure_index(name: str, index: Any, ids: List[str], vectors: np.ndarray,
                  query_vectors: np.ndarray, truth: List[List[int]], k: int,
                  repeats: int) -> Dict[str, Any]:
    build_start = time.perf_counter()
    for doc_id, vector in zip(ids, vectors):
        index.add_item(doc_id, vector)
    index.rebuild_index()
    build_ms = (time.perf_counter() - build_start) * 1000

    id_to_pos = {doc_id: pos for pos, doc_id in enumerate(ids)}
    recalls, latencies = [], []
    rankings = []
    for q_idx, query in enumerate(query_vectors):
        first = None
        for _ in range(repeats):
            started = time.perf_counter()
            found, distances = index.search(query, k)
            latencies.append((time.perf_counter() - started) * 1000)
            if first is None:
                first = found
        found_pos = {id_to_pos[x] for x in first if x in id_to_pos}
        recalls.append(len(found_pos & set(truth[q_idx])) / k)
        rankings.append({"query_index": q_idx, "doc_ids": first})

    with tempfile.NamedTemporaryFile(suffix=f".{name}") as handle:
        if name == "annoy":
            index.index.save(handle.name)
        else:
            index.index.save_index(handle.name)
        serialized_bytes = os.path.getsize(handle.name)
    return {
        "build_ms": round(build_ms, 3),
        "recall_at_k": statistics.mean(recalls),
        "query_latency_ms": percentiles(latencies),
        "serialized_bytes": serialized_bytes,
        "rankings": rankings,
    }


def local_annoy_healthy() -> bool:
    probe = AnnoyIndex(3, n_trees=5)
    for i in range(5):
        probe.add_item(str(i), np.array([i + 1, i + 2, i + 3], dtype="float32"))
    probe.rebuild_index()
    found, _ = probe.search(np.array([2, 3, 4], dtype="float32"), 3)
    return len(found) == 3


def measure_annoy_docker(ids: List[str], vectors: np.ndarray, queries: np.ndarray,
                         initial_truth: List[List[int]], full_truth: List[List[int]],
                         initial_n: int, k: int, repeats: int) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Run the real Spotify ANNOY library in Linux when the macOS ARM extension
    returns only item zero (a reproducible host-wheel defect in this environment)."""
    with tempfile.TemporaryDirectory() as raw_dir:
        work = Path(raw_dir)
        np.savez(
            work / "input.npz",
            ids=np.asarray(ids, dtype="U32"), vectors=vectors, queries=queries,
            initial_truth=np.asarray(initial_truth, dtype="int64"),
            full_truth=np.asarray(full_truth, dtype="int64"),
            parameters=np.asarray([initial_n, k, repeats], dtype="int64"),
        )
        command = [
            "docker", "run", "--rm",
            "-v", f"{work}:/work",
            "-v", f"{HERE / 'docker_annoy_runner.py'}:/runner.py:ro",
            "python:3.11-slim",
            "sh", "-lc",
            "apt-get update -qq && apt-get install -y -qq g++ >/dev/null && "
            "pip install -q numpy annoy && python /runner.py /work/input.npz /work/output.json",
        ]
        started = time.perf_counter()
        proc = subprocess.run(command, text=True, capture_output=True, timeout=600)
        wall_ms = (time.perf_counter() - started) * 1000
        if proc.returncode != 0:
            raise RuntimeError(f"Docker ANNOY runner failed: {proc.stderr[-2000:]}")
        result = json.loads((work / "output.json").read_text(encoding="utf-8"))
    inspect = subprocess.check_output(
        ["docker", "image", "inspect", "python:3.11-slim", "--format", "{{json .RepoDigests}}"],
        text=True,
    ).strip()
    runtime = {
        "kind": "docker-linux-aarch64",
        "reason": "host macOS ARM ANNOY extension failed health check (returned fewer than k items)",
        "base_image": "python:3.11-slim",
        "base_image_repo_digests": json.loads(inspect),
        "container_setup_and_run_wall_ms": round(wall_ms, 3),
    }
    return result, runtime


def main() -> int:
    parser = argparse.ArgumentParser(description="Experiment 3-4 ANNOY/HNSW real embedding benchmark")
    parser.add_argument("--model", default="Qwen/Qwen3-Embedding-0.6B")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--docs", type=int, default=300)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=37)
    args = parser.parse_args()
    np.random.seed(args.seed)

    ids, docs = build_corpus(args.docs)
    queries = [f"Find technical information about {topic}." for topic, _ in TOPICS]
    encoder = TransformerEncoder(args.model, args.device)
    embed_start = time.perf_counter()
    vectors = encoder.encode(docs)
    query_vectors = encoder.encode(queries, query=True)
    embedding_ms = (time.perf_counter() - embed_start) * 1000
    truth = exact_neighbors(vectors, query_vectors, args.top_k)
    dim = vectors.shape[1]

    initial_n = int(args.docs * 0.8)
    initial_truth = exact_neighbors(vectors[:initial_n], query_vectors, args.top_k)
    backends = {
        "hnsw": HNSWIndex(dim, max_elements=args.docs + 10, ef_construction=200, M=16, ef_search=100),
    }
    results = {}
    if local_annoy_healthy():
        backends["annoy"] = AnnoyIndex(dim, n_trees=50, metric="angular")
        annoy_runtime = {"kind": "host", "health_check": "passed"}
    else:
        results["annoy"], annoy_runtime = measure_annoy_docker(
            ids, vectors, query_vectors, initial_truth, truth,
            initial_n, args.top_k, args.repeats,
        )
        print(f"annoy (Docker): recall@{args.top_k}={results['annoy']['recall_at_k']:.3f}, "
              f"build={results['annoy']['build_ms']:.1f}ms")
    for name, backend in backends.items():
        initial = measure_index(
            name, backend, ids[:initial_n], vectors[:initial_n], query_vectors,
            initial_truth, args.top_k, args.repeats,
        )
        update_start = time.perf_counter()
        for doc_id, vector in zip(ids[initial_n:], vectors[initial_n:]):
            backend.add_item(doc_id, vector)
        requires_rebuild = name == "annoy"
        if requires_rebuild:
            backend.rebuild_index()
        update_ms = (time.perf_counter() - update_start) * 1000
        id_to_pos = {doc_id: pos for pos, doc_id in enumerate(ids)}
        update_recalls = []
        for q_idx, query in enumerate(query_vectors):
            found, _ = backend.search(query, args.top_k)
            update_recalls.append(len({id_to_pos[x] for x in found} & set(truth[q_idx])) / args.top_k)
        initial["incremental_update"] = {
            "items_added": args.docs - initial_n,
            "latency_ms": round(update_ms, 3),
            "requires_full_rebuild": requires_rebuild,
            "recall_at_k_after_update": statistics.mean(update_recalls),
        }
        results[name] = initial
        print(f"{name}: recall@{args.top_k}={initial['recall_at_k']:.3f}, build={initial['build_ms']:.1f}ms")

    cache_ref = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{args.model.replace('/', '--')}" / "refs" / "main"
    model_revision = cache_ref.read_text(encoding="utf-8").strip() if cache_ref.exists() else None
    full = args.docs >= 300 and all(results[name]["recall_at_k"] >= 0.8 for name in results)
    evidence = {
        "status": "passed" if full else "partial",
        "configuration": {
            "embedding_model": args.model,
            "model_revision": model_revision,
            "device": args.device,
            "seed": args.seed,
            "dimension": dim,
            "documents": args.docs,
            "queries": len(queries),
            "top_k": args.top_k,
            "annoy_runtime": annoy_runtime,
        },
        "acceptance": {
            "real_embedding_model": True,
            "same_vectors_and_queries": True,
            "exact_search_ground_truth": True,
            "recall_latency_build_size_measured": True,
            "incremental_behavior_measured": True,
            "both_backends_recall_at_least_0_8": all(results[name]["recall_at_k"] >= 0.8 for name in results),
            "passed": full,
        },
        "summary": {
            "embedding_latency_ms": round(embedding_ms, 3),
            "annoy": {k: v for k, v in results["annoy"].items() if k != "rankings"},
            "hnsw": {k: v for k, v in results["hnsw"].items() if k != "rankings"},
        },
        "corpus": {"doc_ids": ids, "texts": docs, "queries": queries},
        "results": results,
    }
    manifest = write_campaign_evidence(
        HERE, "3-4", evidence,
        input_paths=[HERE / "indexing.py", HERE / "benchmark.py", HERE / "docker_annoy_runner.py"]
    )
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
