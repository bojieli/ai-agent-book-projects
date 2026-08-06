#!/usr/bin/env python3
"""Canonical live plain-vs-contextual retrieval campaign (Experiment 3-10)."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
from openai import OpenAI
from rank_bm25 import BM25Okapi

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
sys.path.insert(0, str(CHAPTER))
sys.path.insert(0, str(HERE))

from experiment_utils import ChatRecorder, sha256_file, write_campaign_evidence
from compare_retrieval import tokenize


ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"


class TransformerEncoder:
    def __init__(self, model_name: str, device: str):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.model_name = model_name
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side="left")
        self.model = AutoModel.from_pretrained(model_name).to(device).eval()
        self.revision = getattr(self.model.config, "_commit_hash", None)

    def encode(self, texts: Sequence[str], *, query: bool, batch_size: int = 8) -> np.ndarray:
        prefix = "Instruct: Retrieve semantically relevant passages.\nQuery:" if query else ""
        vectors = []
        for start in range(0, len(texts), batch_size):
            batch = [prefix + text for text in texts[start : start + batch_size]]
            tokens = self.tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors="pt").to(self.device)
            with self.torch.no_grad():
                output = self.model(**tokens).last_hidden_state[:, -1].float()
            output = self.torch.nn.functional.normalize(output, p=2, dim=1)
            vectors.append(output.cpu().numpy())
        return np.concatenate(vectors).astype("float32")


def load_chunks(path: Path) -> List[Dict[str, Any]]:
    store = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for chunk_id, entry in store.items():
        if "_chunk_" not in chunk_id:
            continue
        meta = entry.get("metadata") or {}
        rows.append(
            {
                "chunk_id": chunk_id,
                "doc_title": meta.get("doc_title") or chunk_id.split("_chunk_")[0],
                "plain": meta.get("original_text") or entry.get("content", ""),
            }
        )
    return sorted(rows, key=lambda row: row["chunk_id"])


def source_documents(chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    laws = CHAPTER / "agentic-rag" / "laws"
    output = {}
    for title in sorted({row["doc_title"] for row in chunks}):
        candidates = [path for path in laws.rglob("*.md") if path.stem == title]
        if len(candidates) != 1:
            raise RuntimeError(f"expected one official bundled source for {title!r}, found {len(candidates)}")
        path = candidates[0]
        output[title] = {"path": path, "text": path.read_text(encoding="utf-8")}
    return output


def prefix_one(args: argparse.Namespace, chunk: Dict[str, Any], source: Dict[str, Any]):
    client = OpenAI(api_key=os.environ["ARK_API_KEY"], base_url=args.endpoint, timeout=args.timeout, max_retries=3)
    recorder = ChatRecorder(client, "ark", args.endpoint)
    response = recorder.create(
        purpose=f"3-10 live contextual prefix {chunk['chunk_id']}",
        model=args.context_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "为目标文本块生成简短的中文检索前缀。前缀必须说明该块来自哪份文档、所属章节/条款、"
                    "主体与主题，使孤立文本能被准确检索。不得添加源文没有的事实。只输出前缀，不要解释。"
                ),
            },
            {
                "role": "user",
                "content": f"完整源文档：\n<document>\n{source['text']}\n</document>\n\n目标文本块：\n<chunk>\n{chunk['plain']}\n</chunk>",
            },
        ],
        temperature=0,
        seed=args.seed,
        max_tokens=220,
    )
    prefix = (response.choices[0].message.content or "").strip()
    return {**chunk, "prefix": prefix, "contextual": f"{prefix}\n\n{chunk['plain']}"}, recorder.calls


def rankings_bm25(texts: List[str], queries: List[str]) -> List[List[int]]:
    index = BM25Okapi([tokenize(text) for text in texts])
    return [np.argsort(-index.get_scores(tokenize(query))).tolist() for query in queries]


def rankings_dense(vectors: np.ndarray, query_vectors: np.ndarray) -> List[List[int]]:
    return [np.argsort(-(query @ vectors.T)).tolist() for query in query_vectors]


def rrf(a: List[int], b: List[int], constant: int = 60) -> List[int]:
    scores: Dict[int, float] = {}
    for ranking in (a, b):
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (constant + rank)
    return sorted(scores, key=lambda item: scores[item], reverse=True)


def metrics(rankings: List[List[int]], queries: List[Dict[str, Any]], id_to_pos: Dict[str, int]) -> Dict[str, Any]:
    per_query = []
    reciprocal = []
    for query, ranking in zip(queries, rankings):
        gold = id_to_pos[query["gold_chunk_id"]]
        rank = ranking.index(gold) + 1 if gold in ranking else None
        reciprocal.append(1.0 / rank if rank else 0.0)
        per_query.append(
            {
                "id": query["id"],
                "query": query["query"],
                "gold_chunk_id": query["gold_chunk_id"],
                "rank": rank,
                "top5_chunk_ids": ranking[:5],
            }
        )
    return {
        "n": len(queries),
        "recall_at_k": {str(k): statistics.mean(1.0 if row["rank"] and row["rank"] <= k else 0.0 for row in per_query) for k in (1, 3, 5)},
        "mrr": statistics.mean(reciprocal),
        "per_query": per_query,
    }


def token_usage(receipts: List[Dict[str, Any]]) -> Dict[str, int]:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for call in receipts:
        usage = call.get("usage") or {}
        for key in totals:
            totals[key] += int(usage.get(key) or 0)
    return totals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context-model", default=os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"))
    parser.add_argument("--embedding-model", default="Qwen/Qwen3-Embedding-0.6B")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--endpoint", default=ARK_ENDPOINT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--input-price-per-million-usd", type=float, default=0.11)
    parser.add_argument("--output-price-per-million-usd", type=float, default=1.10)
    args = parser.parse_args()
    if not os.getenv("ARK_API_KEY"):
        raise RuntimeError("ARK_API_KEY is required")

    corpus_path = HERE / "document_store.json"
    eval_path = HERE / "evaluation" / "retrieval_eval.json"
    chunks = load_chunks(corpus_path)
    docs = source_documents(chunks)
    receipts: List[Dict[str, Any]] = []
    contextual: List[Dict[str, Any]] = []
    errors = []
    prefix_start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(prefix_one, args, chunk, docs[chunk["doc_title"]]): chunk["chunk_id"] for chunk in chunks}
        for future in concurrent.futures.as_completed(futures):
            chunk_id = futures[future]
            try:
                row, calls = future.result()
                contextual.append(row)
                receipts.extend(calls)
                print(f"prefix {chunk_id} ({len(contextual)}/{len(chunks)})", flush=True)
            except Exception as exc:
                errors.append({"chunk_id": chunk_id, "type": type(exc).__name__, "error": str(exc)})
    prefix_ms = (time.perf_counter() - prefix_start) * 1000
    contextual.sort(key=lambda row: row["chunk_id"])

    eval_data = json.loads(eval_path.read_text(encoding="utf-8"))
    queries = eval_data["queries"]
    query_texts = [row["query"] for row in queries]
    ids = [row["chunk_id"] for row in contextual]
    id_to_pos = {chunk_id: pos for pos, chunk_id in enumerate(ids)}
    methods: Dict[str, Dict[str, Any]] = {}
    embedding_ms = 0.0
    encoder = None
    if len(contextual) == len(chunks) and not errors:
        plain_texts = [row["plain"] for row in contextual]
        contextual_texts = [row["contextual"] for row in contextual]
        plain_bm25 = rankings_bm25(plain_texts, query_texts)
        contextual_bm25 = rankings_bm25(contextual_texts, query_texts)
        encoder = TransformerEncoder(args.embedding_model, args.device)
        started = time.perf_counter()
        plain_vectors = encoder.encode(plain_texts, query=False)
        contextual_vectors = encoder.encode(contextual_texts, query=False)
        query_vectors = encoder.encode(query_texts, query=True)
        embedding_ms = (time.perf_counter() - started) * 1000
        plain_dense = rankings_dense(plain_vectors, query_vectors)
        contextual_dense = rankings_dense(contextual_vectors, query_vectors)
        ranking_sets = {
            "plain_bm25": plain_bm25,
            "contextual_bm25": contextual_bm25,
            "plain_dense": plain_dense,
            "contextual_dense": contextual_dense,
            "plain_hybrid": [rrf(a, b) for a, b in zip(plain_bm25, plain_dense)],
            "contextual_hybrid": [rrf(a, b) for a, b in zip(contextual_bm25, contextual_dense)],
        }
        for name, ranking in ranking_sets.items():
            result = metrics(ranking, queries, id_to_pos)
            for row in result["per_query"]:
                row["top5_chunk_ids"] = [ids[pos] for pos in row["top5_chunk_ids"]]
            methods[name] = result

    tokens = token_usage(receipts)
    estimated_cost = tokens["prompt_tokens"] / 1_000_000 * args.input_price_per_million_usd + tokens["completion_tokens"] / 1_000_000 * args.output_price_per_million_usd
    acceptance = {
        "live_prefix_for_every_chunk": len(contextual) == len(chunks) and all(row["prefix"] for row in contextual),
        "full_source_document_and_target_chunk_in_requests": len(receipts) == len(chunks) and all("<document>" in json.dumps(call.get("request", {}), ensure_ascii=False) and "<chunk>" in json.dumps(call.get("request", {}), ensure_ascii=False) for call in receipts),
        "same_chunks_and_queries": bool(methods) and all(result["n"] == len(queries) for result in methods.values()),
        "plain_contextual_bm25_dense_hybrid": set(methods) == {"plain_bm25", "contextual_bm25", "plain_dense", "contextual_dense", "plain_hybrid", "contextual_hybrid"},
        "recall_and_mrr_measured": bool(methods) and all("mrr" in result and set(result["recall_at_k"]) == {"1", "3", "5"} for result in methods.values()),
        "real_dense_model": bool(encoder and encoder.revision),
        "index_usage_and_cost_measured": tokens["total_tokens"] > 0 and estimated_cost >= 0,
        "raw_request_response_receipts": len(receipts) == len(chunks) and all("request" in call and "response" in call for call in receipts),
        "all_calls_succeeded": not errors,
    }
    acceptance["passed"] = all(acceptance.values())
    evidence = {
        "status": "passed" if acceptance["passed"] else ("partial" if contextual else "blocked"),
        "configuration": vars(args) | {"embedding_revision": getattr(encoder, "revision", None)},
        "scope": {"documents": len(docs), "chunks": len(chunks), "queries": len(queries)},
        "acceptance": acceptance,
        "summary": {
            "methods": {name: {key: value for key, value in result.items() if key != "per_query"} for name, result in methods.items()},
            "index_time": {
                "context_generation_ms": round(prefix_ms, 3),
                "embedding_ms": round(embedding_ms, 3),
                "usage": tokens,
                "estimated_cost_usd": round(estimated_cost, 6),
                "pricing_assumption": {"input_per_million_usd": args.input_price_per_million_usd, "output_per_million_usd": args.output_price_per_million_usd},
            },
            "errors": len(errors),
        },
        "errors": errors,
        "source_documents": {title: {"path": str(data["path"]), "sha256": sha256_file(data["path"])} for title, data in docs.items()},
        "chunks": contextual,
        "results": methods,
    }
    manifest = write_campaign_evidence(
        HERE,
        "3-10",
        evidence,
        receipts,
        input_paths=[HERE / "campaign.py", HERE / "compare_retrieval.py", corpus_path, eval_path, *[data["path"] for data in docs.values()]],
    )
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    print(f"Canonical evidence: {HERE / 'validation' / 'latest.json'}")
    return 0 if acceptance["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
