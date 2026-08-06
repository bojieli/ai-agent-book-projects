#!/usr/bin/env python3
"""Shared canonical campaign for Experiments 3-9 and 3-11.

Experiment 3-9 is the plain fixed-window, agent-searched arm.  Experiment
3-11 replays the exact same live agent-generated queries against plain and
live-contextualized indexes, then adds the live Advanced JSON Cards produced by
Experiment 3-1 as the dual-layer ablation.  This keeps the retrieval plan and
answer/judge models fixed across the three 3-11 arms.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import statistics
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

import numpy as np
import yaml
from openai import OpenAI
from rank_bm25 import BM25Okapi

CHAPTER = Path(__file__).resolve().parent
PLAIN_PROJECT = CHAPTER / "agentic-rag-for-user-memory"
CONTEXT_PROJECT = CHAPTER / "contextual-retrieval-for-user-memory"
SUITE = CHAPTER / "user-memory-evaluation" / "test_cases"
MEMORY_CHECKPOINTS = CHAPTER / "user-memory" / "validation" / "checkpoints" / "full-60x4"
sys.path.insert(0, str(CHAPTER))

from experiment_utils import ChatRecorder, jsonable, sha256_file, write_campaign_evidence


ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"
MOONSHOT_ENDPOINT = "https://api.moonshot.cn/v1"


def parse_json(text: str) -> Dict[str, Any]:
    value = (text or "").strip()
    if "```" in value:
        value = value.split("```", 2)[1]
        if value.lstrip().startswith("json"):
            value = value.lstrip()[4:]
    return json.loads(value.strip())


def load_cases() -> List[Dict[str, Any]]:
    cases = []
    for path in sorted(SUITE.glob("layer*/*.yaml")):
        case = yaml.safe_load(path.read_text(encoding="utf-8"))
        case["_path"] = str(path.resolve())
        cases.append(case)
    return cases


def format_history(history: Dict[str, Any]) -> str:
    lines = [
        f"conversation_id={history.get('conversation_id')}",
        f"timestamp={history.get('timestamp')}",
        f"metadata={json.dumps(history.get('metadata') or {}, ensure_ascii=False)}",
    ]
    for message in history.get("messages", []):
        lines.append(f"{str(message.get('role', '')).upper()}: {message.get('content', '')}")
    return "\n".join(lines)


def fixed_window_chunks(case: Dict[str, Any], rounds_per_chunk: int, overlap_rounds: int) -> List[Dict[str, Any]]:
    output = []
    step = max(1, rounds_per_chunk - overlap_rounds)
    for history in case["conversation_histories"]:
        messages = history.get("messages", [])
        rounds, current = [], []
        for message in messages:
            current.append(message)
            if message.get("role") == "assistant":
                rounds.append(current)
                current = []
        if current:
            rounds.append(current)
        for start in range(0, len(rounds), step):
            selected = rounds[start : start + rounds_per_chunk]
            if not selected:
                continue
            flat = [message for round_messages in selected for message in round_messages]
            chunk_index = len([row for row in output if row["conversation_id"] == history["conversation_id"]])
            chunk_id = f"{case['test_id']}--{history['conversation_id']}--window-{chunk_index:03d}"
            text = "\n".join(
                [
                    f"conversation_id={history['conversation_id']}",
                    f"timestamp={history.get('timestamp')}",
                    f"rounds={start + 1}-{start + len(selected)}",
                    f"metadata={json.dumps(history.get('metadata') or {}, ensure_ascii=False)}",
                    *[f"{str(message.get('role', '')).upper()}: {message.get('content', '')}" for message in flat],
                ]
            )
            output.append(
                {
                    "chunk_id": chunk_id,
                    "conversation_id": history["conversation_id"],
                    "start_round": start + 1,
                    "end_round": start + len(selected),
                    "text": text,
                }
            )
            if start + rounds_per_chunk >= len(rounds):
                break
    return output


class BM25Memory:
    def __init__(self, chunks: List[Dict[str, Any]], field: str):
        self.chunks = chunks
        self.index = BM25Okapi([self.tokenize(row[field]) for row in chunks])
        self.field = field

    @staticmethod
    def tokenize(text: str) -> List[str]:
        import re
        words = re.findall(r"[a-zA-Z0-9_.$@:/-]+|[一-鿿]", (text or "").lower())
        return words

    def search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        scores = self.index.get_scores(self.tokenize(query))
        order = np.argsort(-scores)[:top_k]
        return [
            {
                "rank": rank,
                "score": float(scores[pos]),
                "chunk_id": self.chunks[pos]["chunk_id"],
                "conversation_id": self.chunks[pos]["conversation_id"],
                "start_round": self.chunks[pos]["start_round"],
                "end_round": self.chunks[pos]["end_round"],
                "raw_chunk": self.chunks[pos]["text"],
                "indexed_text": self.chunks[pos][self.field],
            }
            for rank, pos in enumerate(order, start=1)
        ]


def successful_calls(calls: List[Dict[str, Any]]) -> bool:
    return bool(calls) and all("response" in call and "error" not in call for call in calls)


def load_advanced_card(case: Dict[str, Any]) -> Dict[str, Any]:
    path = MEMORY_CHECKPOINTS / f"{case['test_id']}--advanced_json_cards.json"
    if not path.exists():
        raise RuntimeError(f"missing live Advanced JSON Card checkpoint: {path}")
    checkpoint = json.loads(path.read_text(encoding="utf-8"))
    if checkpoint.get("status") != "completed" or not checkpoint.get("result"):
        raise RuntimeError(f"incomplete live Advanced JSON Card checkpoint: {path}")
    states = checkpoint["result"].get("memory_states") or []
    writer_calls = checkpoint.get("writer_calls") or []
    if not states or not successful_calls(writer_calls):
        raise RuntimeError(f"card checkpoint lacks live state/receipts: {path}")
    return {
        "memory": states[-1]["memory"],
        "checkpoint": str(path.resolve()),
        "checkpoint_sha256": sha256_file(path),
        "writer_provider": "ark",
        "writer_endpoint": checkpoint["signature"]["writer_endpoint"],
        "writer_model": checkpoint["signature"]["writer_model"],
        "writer_call_count": len(writer_calls),
        "live_receipts_present": True,
    }


def prefix_prompt(case: Dict[str, Any], chunks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    targets = [{"chunk_id": row["chunk_id"], "raw_chunk": row["text"]} for row in chunks]
    return [
        {
            "role": "system",
            "content": (
                "Generate a concise retrieval prefix for every fixed-window conversation chunk. "
                "Use the entire supplied case as context. Preserve who, which entity/account/item, date, status, "
                "superseded instruction, and cross-session relationship. Do not invent facts. Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"CASE ID: {case['test_id']}\nTITLE: {case['title']}\n"
                f"FULL CASE CHUNKS (collectively the full source):\n{json.dumps(targets, ensure_ascii=False)}\n\n"
                'Return exactly {"prefixes":{"chunk_id":"prefix",...}} with every supplied chunk_id once.'
            ),
        },
    ]


def contextualize(case: Dict[str, Any], chunks: List[Dict[str, Any]], recorder: ChatRecorder, args: argparse.Namespace) -> List[Dict[str, Any]]:
    prefixes: Dict[str, Any] = {}
    missing = [row["chunk_id"] for row in chunks]
    for attempt in range(1, 4):
        messages = prefix_prompt(case, chunks)
        if attempt > 1:
            messages[1]["content"] += (
                "\n\nREPAIR: The prior response omitted these IDs. Return prefixes for every listed ID: "
                + json.dumps(missing, ensure_ascii=False)
            )
        response = recorder.create(
            purpose=f"3-12 live contextual prefixes {case['test_id']} attempt {attempt}",
            model=args.answer_model,
            messages=messages,
            temperature=0,
            seed=args.seed,
            max_tokens=5000,
            response_format={"type": "json_object"},
        )
        parsed = parse_json(response.choices[0].message.content or "{}")
        prefixes.update(parsed.get("prefixes") or {})
        missing = [row["chunk_id"] for row in chunks if not str(prefixes.get(row["chunk_id"], "")).strip()]
        if not missing:
            break
    if missing:
        raise RuntimeError(f"live prefix response omitted {len(missing)} chunks: {missing[:3]}")
    return [{**row, "prefix": str(prefixes[row["chunk_id"]]).strip(), "contextual": f"{prefixes[row['chunk_id']]}\n\n{row['text']}"} for row in chunks]


SEARCH_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "search_user_memory",
            "description": "Search fixed-window chunks from the user's prior conversations.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "A focused memory search query"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    }
]


def live_search_plan(case: Dict[str, Any], index: BM25Memory, recorder: ChatRecorder, args: argparse.Namespace):
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a ReAct memory-search planner. Use search_user_memory to gather every fact needed for the question. "
                "Inspect tool results, then iterate with a different focused query when one search is incomplete, ambiguous, "
                "or misses a cross-session dependency. Layer-2/3 questions normally need multiple focused searches. "
                "Do not answer the user; when evidence is sufficient, say SEARCH_COMPLETE."
            ),
        },
        {"role": "user", "content": f"CASE LAYER: {case['category']}\nQUESTION: {case['user_question']}"},
    ]
    trajectory = []
    queries = []
    for iteration in range(1, args.max_searches + 2):
        response = recorder.create(
            purpose=f"3-10 live ReAct search planner {case['test_id']} iteration {iteration}",
            model=args.answer_model,
            messages=messages,
            tools=SEARCH_TOOL,
            tool_choice="required" if iteration == 1 else "auto",
            temperature=0,
            seed=args.seed,
            max_tokens=700,
        )
        message = response.choices[0].message
        assistant: Dict[str, Any] = {"role": "assistant", "content": message.content or ""}
        if message.tool_calls:
            assistant["tool_calls"] = [jsonable(call) for call in message.tool_calls]
        messages.append(assistant)
        step = {"iteration": iteration, "assistant": message.content or "", "tool_calls": []}
        if not message.tool_calls:
            trajectory.append(step)
            break
        for call in message.tool_calls:
            if len(queries) >= args.max_searches:
                payload = {"error": "search budget exhausted"}
            else:
                try:
                    query = str(json.loads(call.function.arguments).get("query", "")).strip()
                except Exception:
                    query = ""
                if not query:
                    payload = {"error": "empty query"}
                else:
                    results = index.search(query, args.top_k)
                    queries.append(query)
                    payload = {"query": query, "results": results}
                    step["tool_calls"].append(payload)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(payload, ensure_ascii=False)})
        trajectory.append(step)
        if len(queries) >= args.max_searches:
            break
    if not queries:
        raise RuntimeError("ReAct planner produced no memory search")
    return queries, trajectory


def union_search(index: BM25Memory, queries: List[str], top_k: int) -> List[Dict[str, Any]]:
    best: Dict[str, Dict[str, Any]] = {}
    for query in queries:
        for row in index.search(query, top_k):
            item = {**row, "search_query": query}
            old = best.get(row["chunk_id"])
            if old is None or row["score"] > old["score"]:
                best[row["chunk_id"]] = item
    return sorted(best.values(), key=lambda row: row["score"], reverse=True)[: max(top_k, top_k * len(queries))]


def answer_prompt(case: Dict[str, Any], arm: str, retrieved: List[Dict[str, Any]], card: Dict[str, Any] | None):
    evidence = "\n\n".join(f"[{row['chunk_id']}]\n{row['raw_chunk']}" for row in retrieved)
    card_text = json.dumps(card["memory"], ensure_ascii=False) if card else "(none)"
    return [
        {
            "role": "system",
            "content": (
                "You are in a brand-new session. Answer only from retrieved conversation evidence and, in the dual arm, "
                "the structured memory card. Resolve entity ambiguity and superseded instructions, connect sessions, and "
                "proactively surface material risks. Cite raw evidence as [chunk_id]. Do not invent facts."
            ),
        },
        {
            "role": "user",
            "content": f"ARM: {arm}\nQUESTION: {case['user_question']}\n\nADVANCED JSON CARD:\n{card_text}\n\nRETRIEVED RAW CHUNKS:\n{evidence}",
        },
    ]


def judge_prompt(case: Dict[str, Any], answers: Dict[str, str]) -> List[Dict[str, str]]:
    source = "\n\n".join(format_history(history) for history in case["conversation_histories"])
    return [
        {
            "role": "system",
            "content": (
                "You are the strict independent judge for a memory-system ablation. Grade each arm independently against "
                "the authoritative source. Score precision, recall, reasoning and proactivity 1-4. A material unsupported "
                "or contradicted claim is a hallucination veto. Return JSON only."
            ),
        },
        {
            "role": "user",
            "content": f"""AUTHORITATIVE SOURCE:
{source}

QUESTION: {case['user_question']}
CRITERIA: {case['evaluation_criteria']}
EXPECTED: {case.get('expected_behavior', '')}

ANSWERS BY ARM:
{json.dumps(answers, ensure_ascii=False)}

Return {{"arms":{{"plain":{{"dimensions":{{"precision":1,"recall":1,"reasoning":1,"proactivity":1}},"hallucination":false,"reasoning":"..."}},
"contextual":{{same fields}},"dual_layer":{{same fields}}}}}}. Use integers 1-4.""",
        },
    ]


def summarize_judge(raw: Dict[str, Any], arm: str) -> Dict[str, Any]:
    item = (raw.get("arms") or {}).get(arm) or {}
    dimensions = item.get("dimensions") or {}
    scores = {name: min(4, max(1, int(dimensions.get(name, 1)))) for name in ("precision", "recall", "reasoning", "proactivity")}
    hallucination = bool(item.get("hallucination"))
    return {
        "scores": scores,
        "hallucination_veto": hallucination,
        "passed": not hallucination and all(scores[name] >= 3 for name in ("precision", "recall", "reasoning")),
        "reward": 0.0 if hallucination else statistics.mean(scores.values()) / 4.0,
        "reasoning": item.get("reasoning", ""),
    }


class Campaign:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.checkpoints = CONTEXT_PROJECT / "validation" / "checkpoints" / "full-60"
        self.checkpoints.mkdir(parents=True, exist_ok=True)
        suite_hash = hashlib.sha256("".join(sha256_file(path) for path in sorted(SUITE.glob("layer*/*.yaml"))).encode()).hexdigest()
        self.signature = {
            "suite_hash": suite_hash,
            "answer_model": args.answer_model,
            "judge_model": args.judge_model,
            "seed": args.seed,
            "rounds_per_chunk": args.rounds_per_chunk,
            "overlap_rounds": args.overlap_rounds,
            "top_k": args.top_k,
            "max_searches": args.max_searches,
        }

    def checkpoint_path(self, case: Dict[str, Any]) -> Path:
        return self.checkpoints / f"{case['test_id']}.json"

    def run_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        checkpoint_path = self.checkpoint_path(case)
        if checkpoint_path.exists():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint.get("signature") != self.signature:
                raise RuntimeError(f"checkpoint signature mismatch: {checkpoint_path}")
            if checkpoint.get("status") == "completed":
                return {**checkpoint["result"], "_receipts": checkpoint["receipts"], "_resumed": True}

        # Fail before any new API call when the upstream live-card dependency
        # is not complete.  This makes the campaign safely resumable while the
        # 3-1 card arm is still filling its own checkpoints.
        card = load_advanced_card(case)
        answer_client = OpenAI(api_key=os.environ["ARK_API_KEY"], base_url=self.args.answer_endpoint, timeout=self.args.timeout, max_retries=3)
        judge_key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
        judge_client = OpenAI(api_key=judge_key, base_url=self.args.judge_endpoint, timeout=self.args.timeout, max_retries=3)
        answer_recorder = ChatRecorder(answer_client, "ark", self.args.answer_endpoint)
        judge_recorder = ChatRecorder(judge_client, "moonshot", self.args.judge_endpoint)
        chunks = fixed_window_chunks(case, self.args.rounds_per_chunk, self.args.overlap_rounds)
        contextual_chunks = contextualize(case, chunks, answer_recorder, self.args)
        plain_index = BM25Memory([{**row, "plain": row["text"]} for row in chunks], "plain")
        contextual_index = BM25Memory(contextual_chunks, "contextual")
        queries, trajectory = live_search_plan(case, plain_index, answer_recorder, self.args)
        plain_results = union_search(plain_index, queries, self.args.top_k)
        contextual_results = union_search(contextual_index, queries, self.args.top_k)
        arms = {
            "plain": {"retrieved_chunks": plain_results, "card": None},
            "contextual": {"retrieved_chunks": contextual_results, "card": None},
            "dual_layer": {"retrieved_chunks": contextual_results, "card": card},
        }
        answers = {}
        for arm, payload in arms.items():
            response = answer_recorder.create(
                purpose=f"3-12 grounded answer {case['test_id']} {arm}",
                model=self.args.answer_model,
                messages=answer_prompt(case, arm, payload["retrieved_chunks"], payload["card"]),
                temperature=0,
                seed=self.args.seed,
                max_tokens=1400,
            )
            answers[arm] = response.choices[0].message.content or ""
        response = judge_recorder.create(
            purpose=f"3-10/3-12 independent judge {case['test_id']}",
            model=self.args.judge_model,
            messages=judge_prompt(case, answers),
            temperature=0,
            seed=self.args.seed,
            max_tokens=1800,
            response_format={"type": "json_object"},
        )
        judge_raw = parse_json(response.choices[0].message.content or "{}")
        for arm in arms:
            arms[arm]["answer"] = answers[arm]
            arms[arm]["judge"] = summarize_judge(judge_raw, arm)
        result = {
            "test_id": case["test_id"],
            "layer": case["category"],
            "title": case["title"],
            "question": case["user_question"],
            "chunking": {"strategy": "fixed_round_window", "rounds_per_chunk": self.args.rounds_per_chunk, "overlap_rounds": self.args.overlap_rounds, "chunks": chunks},
            "live_prefixes": [{"chunk_id": row["chunk_id"], "prefix": row["prefix"]} for row in contextual_chunks],
            "agent_search_queries": queries,
            "search_trajectory": trajectory,
            "advanced_card_provenance": {key: value for key, value in card.items() if key != "memory"},
            "arms": arms,
            "judge_raw": judge_raw,
        }
        receipts = answer_recorder.calls + judge_recorder.calls
        payload = {"signature": self.signature, "status": "completed", "result": result, "receipts": receipts}
        temporary = checkpoint_path.with_suffix(f".{threading.get_ident()}.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(checkpoint_path)
        return {**result, "_receipts": receipts, "_resumed": False}


def aggregate(rows: List[Dict[str, Any]], arms: Iterable[str]) -> Dict[str, Any]:
    output = {}
    for arm in arms:
        output[arm] = {}
        for layer in ("layer1", "layer2", "layer3", "overall"):
            selected = rows if layer == "overall" else [row for row in rows if row["layer"] == layer]
            output[arm][layer] = {
                "n": len(selected),
                "pass_rate": statistics.mean(1.0 if row["arms"][arm]["judge"]["passed"] else 0.0 for row in selected),
                "mean_reward": statistics.mean(row["arms"][arm]["judge"]["reward"] for row in selected),
                "hallucination_rate": statistics.mean(1.0 if row["arms"][arm]["judge"]["hallucination_veto"] else 0.0 for row in selected),
            }
    return output


def token_usage(receipts: List[Dict[str, Any]]) -> Dict[str, int]:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for call in receipts:
        current = call.get("usage") or {}
        for key in totals:
            totals[key] += int(current.get(key) or 0)
    return totals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--answer-model", default=os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"))
    parser.add_argument("--judge-model", default=os.getenv("MEMORY_JUDGE_MODEL", "moonshot-v1-32k"))
    parser.add_argument("--answer-endpoint", default=ARK_ENDPOINT)
    parser.add_argument("--judge-endpoint", default=MOONSHOT_ENDPOINT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--rounds-per-chunk", type=int, default=8)
    parser.add_argument("--overlap-rounds", type=int, default=2)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--max-searches", type=int, default=3)
    args = parser.parse_args()
    if not os.getenv("ARK_API_KEY") or not (os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")):
        raise RuntimeError("ARK_API_KEY and MOONSHOT_API_KEY/KIMI_API_KEY are required")
    cases = load_cases()
    if len(cases) != 60:
        raise RuntimeError(f"authoritative suite must have 60 cases, found {len(cases)}")

    campaign = Campaign(args)
    rows, receipts, errors = [], [], []
    resumed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(campaign.run_case, case): case["test_id"] for case in cases}
        for future in concurrent.futures.as_completed(futures):
            test_id = futures[future]
            try:
                row = future.result()
                receipts.extend(row.pop("_receipts"))
                resumed += int(row.pop("_resumed"))
                rows.append(row)
                print(f"completed {test_id} ({len(rows)}/60)", flush=True)
            except Exception as exc:
                errors.append({"test_id": test_id, "type": type(exc).__name__, "error": str(exc)})
                print(f"ERROR {test_id}: {exc}", file=sys.stderr, flush=True)
    rows.sort(key=lambda row: row["test_id"])
    layer_counts = {layer: sum(row["layer"] == layer for row in rows) for layer in ("layer1", "layer2", "layer3")}
    checkpoints = [Path(row["advanced_card_provenance"]["checkpoint"]) for row in rows]
    receipts_310 = [
        call for call in receipts
        if "3-10 live ReAct search planner" in str(call.get("purpose", ""))
        or (
            "3-12 grounded answer" in str(call.get("purpose", ""))
            and str(call.get("purpose", "")).endswith(" plain")
        )
        or "3-10/3-12 independent judge" in str(call.get("purpose", ""))
    ]
    common = {
        "all_60_cases": len(rows) == 60,
        "twenty_per_layer": layer_counts == {"layer1": 20, "layer2": 20, "layer3": 20},
        "fixed_window_indexing": bool(rows) and all(row["chunking"]["strategy"] == "fixed_round_window" and row["chunking"]["chunks"] for row in rows),
        "live_agent_generated_searches": bool(rows) and all(row["agent_search_queries"] for row in rows),
        "raw_chunks_and_trajectories_retained": bool(rows) and all(row["search_trajectory"] and row["arms"]["plain"]["retrieved_chunks"] for row in rows),
        "independent_external_judge": any(call.get("provider") == "moonshot" for call in receipts),
        "raw_request_response_receipts": bool(receipts) and all("request" in call and "response" in call for call in receipts),
        "all_calls_succeeded": not errors,
    }
    acceptance_310 = {
        **common,
        "same_three_layer_judge_metrics": bool(rows) and all(set(row["arms"]["plain"]["judge"]["scores"]) == {"precision", "recall", "reasoning", "proactivity"} for row in rows),
        "agent_can_iterate": any(len(row["agent_search_queries"]) > 1 for row in rows),
        "canonical_receipts_cover_planner_answer_and_joint_judge": (
            any("3-10 live ReAct search planner" in str(call.get("purpose", "")) for call in receipts_310)
            and any(str(call.get("purpose", "")).endswith(" plain") for call in receipts_310)
            and any("3-10/3-12 independent judge" in str(call.get("purpose", "")) for call in receipts_310)
        ),
    }
    acceptance_310["passed"] = all(acceptance_310.values())
    acceptance_312 = {
        **common,
        "contradictory_financial_case": any(row["test_id"] == "layer2_12_contradictory_financial_instructions" for row in rows),
        "proactive_travel_case": any(row["test_id"] == "layer3_01_travel_coordination" for row in rows),
        "live_prefix_for_every_chunk": bool(rows) and all(len(row["live_prefixes"]) == len(row["chunking"]["chunks"]) and all(item["prefix"] for item in row["live_prefixes"]) for row in rows),
        "live_advanced_cards_with_receipt_provenance": bool(rows) and all(row["advanced_card_provenance"]["live_receipts_present"] for row in rows),
        "plain_contextual_dual_ablation": bool(rows) and all(set(row["arms"]) == {"plain", "contextual", "dual_layer"} for row in rows),
        "identical_live_queries_across_arms": bool(rows),
        "same_three_layer_judge_metrics": bool(rows) and all(all(set(row["arms"][arm]["judge"]["scores"]) == {"precision", "recall", "reasoning", "proactivity"} for arm in row["arms"]) for row in rows),
    }
    acceptance_312["passed"] = all(acceptance_312.values())
    summary_310 = {"aggregate": aggregate(rows, ["plain"]), "api_calls": len(receipts_310), "token_usage": token_usage(receipts_310), "errors": len(errors), "resumed_cases": resumed}
    summary_312 = {"aggregate": aggregate(rows, ["plain", "contextual", "dual_layer"]), "api_calls": len(receipts), "token_usage": token_usage(receipts), "errors": len(errors), "resumed_cases": resumed}
    evidence_310 = {
        "status": "passed" if acceptance_310["passed"] else ("partial" if rows else "blocked"),
        "configuration": vars(args),
        "scope": {"cases": len(rows), "layer_counts": layer_counts},
        "acceptance": acceptance_310,
        "summary": summary_310,
        "errors": errors,
        "results": [{key: value for key, value in row.items() if key not in ("live_prefixes", "advanced_card_provenance") } | {"arms": {"plain": row["arms"]["plain"]}} for row in rows],
    }
    evidence_312 = {
        "status": "passed" if acceptance_312["passed"] else ("partial" if rows else "blocked"),
        "configuration": vars(args),
        "scope": {"cases": len(rows), "layer_counts": layer_counts},
        "acceptance": acceptance_312,
        "summary": summary_312,
        "errors": errors,
        "results": rows,
    }
    yaml_paths = [case["_path"] for case in cases]
    write_campaign_evidence(
        PLAIN_PROJECT,
        "3-10",
        evidence_310,
        receipts_310,
        input_paths=[CHAPTER / "memory_rag_campaign.py", PLAIN_PROJECT / "campaign.py", *yaml_paths],
    )
    manifest = write_campaign_evidence(
        CONTEXT_PROJECT,
        "3-12",
        evidence_312,
        receipts,
        input_paths=[CHAPTER / "memory_rag_campaign.py", CONTEXT_PROJECT / "campaign.py", *yaml_paths, *checkpoints],
    )
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    print(f"Canonical evidence: {PLAIN_PROJECT / 'validation' / 'latest.json'}")
    print(f"Canonical evidence: {CONTEXT_PROJECT / 'validation' / 'latest.json'}")
    return 0 if acceptance_310["passed"] and acceptance_312["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
