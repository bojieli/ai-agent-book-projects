#!/usr/bin/env python3
"""Live sequential-memory campaign for Experiments 3-1 and 3-2.

Unlike the offline keyword fixture, this runner sends every historical session
to a real memory writer one at a time.  From session two onward the writer is
given only the previous *memory state* and the new session; prior raw sessions
are deliberately absent.  A fresh answer is then generated from memory alone
and graded by a different provider/model.

The default is a six-case smoke campaign (two per layer). Use ``--all`` for the
authoritative 60-case × four-mode comparison required by the manuscript.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import statistics
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml
from openai import OpenAI

HERE = Path(__file__).resolve().parent
CHAPTER = HERE.parent
sys.path.insert(0, str(CHAPTER))
from experiment_utils import ChatRecorder, jsonable, sha256_file, write_campaign_evidence


ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3"
MOONSHOT_ENDPOINT = "https://api.moonshot.cn/v1"
MODES = ("notes", "enhanced_notes", "json_cards", "advanced_json_cards")

MODE_INSTRUCTIONS = {
    "notes": (
        "Store memory as an array of minimal standalone factual notes. Split a "
        "complex statement into atomic facts; keep exact names, identifiers and dates."
    ),
    "enhanced_notes": (
        "Store memory as an array of contextual paragraphs. Each paragraph must retain "
        "the entity, event, time, status, and relationships needed to interpret it."
    ),
    "json_cards": (
        "Store memory as a hierarchical JSON object using category/subcategory/key/value "
        "organization. Preserve multi-entity distinctions and historical status."
    ),
    "advanced_json_cards": (
        "Store memory as an array of cards. Every card must include category, card_key, "
        "backstory, person, relationship, timestamp, status, and a facts object. Keep "
        "conflicting instructions as ordered versions rather than silently merging them."
    ),
}


def parse_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if "```" in text:
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def load_cases(root: Path, args: argparse.Namespace) -> List[Dict[str, Any]]:
    paths = sorted(root.glob("layer*/*.yaml"))
    cases = []
    wanted = set(args.case or [])
    by_layer: Dict[str, int] = defaultdict(int)
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if wanted and data.get("test_id") not in wanted:
            continue
        layer = data.get("category")
        if not args.all and not wanted and by_layer[layer] >= args.per_layer:
            continue
        data["_path"] = str(path.resolve())
        cases.append(data)
        by_layer[layer] += 1
    if wanted:
        missing = wanted - {c["test_id"] for c in cases}
        if missing:
            raise ValueError(f"Unknown test ids: {sorted(missing)}")
    return cases


def format_history(history: Dict[str, Any]) -> str:
    metadata = json.dumps(history.get("metadata") or {}, ensure_ascii=False)
    lines = [
        f"conversation_id={history.get('conversation_id')}",
        f"timestamp={history.get('timestamp')}",
        f"metadata={metadata}",
    ]
    for message in history.get("messages", []):
        lines.append(f"{str(message.get('role', '')).upper()}: {message.get('content', '')}")
    return "\n".join(lines)


def initial_memory(mode: str) -> Any:
    return [] if mode != "json_cards" else {}


def memory_prompt(mode: str, memory: Any, history: Dict[str, Any], session_index: int) -> List[Dict[str, str]]:
    system = (
        "You are a long-term memory writer. Select only facts that may help a future "
        "assistant, but retain exact values, ownership, event status, dates, provenance, "
        "and relationships. Apply updates without losing still-valid facts. Never answer "
        "the conversation. Return JSON only as {\"memory\": ...}. " + MODE_INSTRUCTIONS[mode]
    )
    user = (
        f"MEMORY MODE: {mode}\nSESSION INDEX: {session_index}\n\n"
        "CURRENT MEMORY STATE (the only retained information from older sessions):\n"
        f"{json.dumps(memory, ensure_ascii=False)}\n\n"
        "NEW SESSION (analyze this session, then replace the memory state):\n"
        f"{format_history(history)}"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def answer_prompt(mode: str, memory: Any, question: str) -> List[Dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are an assistant in a brand-new session. The supplied long-term memory "
                "is your only source about this user: you cannot access earlier raw dialogue. "
                "Answer accurately, resolve ambiguity, connect sessions, and proactively warn "
                "about material risks. Do not invent facts."
            ),
        },
        {
            "role": "user",
            "content": (
                f"MEMORY MODE: {mode}\nLONG-TERM MEMORY:\n"
                f"{json.dumps(memory, ensure_ascii=False)}\n\nUSER QUESTION:\n{question}"
            ),
        },
    ]


def judge_prompt(case: Dict[str, Any], answer: str) -> List[Dict[str, str]]:
    source = "\n\n".join(format_history(h) for h in case["conversation_histories"])
    system = (
        "You are a strict independent judge of a memory assistant. Use only the authoritative "
        "conversation source. Score precision, recall, reasoning, and proactivity from 1 to 4. "
        "A material unsupported or contradicted factual claim is a hallucination veto. Return "
        "JSON only."
    )
    user = f"""AUTHORITATIVE SOURCE:
{source}

QUESTION: {case['user_question']}
ANSWER: {answer}
EVALUATION CRITERIA: {case['evaluation_criteria']}
EXPECTED BEHAVIOR: {case.get('expected_behavior', '')}

Return exactly:
{{"dimensions": {{"precision": {{"score": 1, "reasoning": "...", "evidence": []}},
"recall": {{"score": 1, "reasoning": "...", "evidence": []}},
"reasoning": {{"score": 1, "reasoning": "...", "evidence": []}},
"proactivity": {{"score": 1, "reasoning": "...", "evidence": []}}}},
"hallucination": {{"detected": false, "claims": [], "reasoning": "..."}},
"overall_reasoning": "..."}}

Scale: 4 fully meets the concrete criterion; 3 meets the core with only a minor
defect; 2 has a material omission; 1 misses/contradicts the core. Asking a
targeted clarification is correct when several entities plausibly match.
"""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def judge_summary(raw: Dict[str, Any]) -> Dict[str, Any]:
    dims = raw.get("dimensions") or {}
    scores = {}
    for name in ("precision", "recall", "reasoning", "proactivity"):
        score = int((dims.get(name) or {}).get("score", 1))
        scores[name] = min(4, max(1, score))
    hallucination = bool((raw.get("hallucination") or {}).get("detected"))
    passed = not hallucination and all(scores[x] >= 3 for x in ("precision", "recall", "reasoning"))
    reward = 0.0 if hallucination else statistics.mean(scores.values()) / 4.0
    return {"scores": scores, "hallucination_veto": hallucination, "passed": passed, "reward": reward}


class Campaign:
    def __init__(self, args: argparse.Namespace):
        ark_key = os.getenv("ARK_API_KEY") or os.getenv("DOUBAO_API_KEY")
        moonshot_key = os.getenv("MOONSHOT_API_KEY")
        if not ark_key or not moonshot_key:
            raise RuntimeError("ARK_API_KEY and MOONSHOT_API_KEY are both required")
        self.args = args
        self.writer_client = OpenAI(
            api_key=ark_key, base_url=args.writer_endpoint, timeout=args.timeout, max_retries=3
        )
        self.judge_client = OpenAI(
            api_key=moonshot_key, base_url=args.judge_endpoint, timeout=args.timeout, max_retries=3
        )
        self.checkpoint_dir = args.checkpoint_dir.resolve()
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_signature = {
            "writer_endpoint": args.writer_endpoint,
            "writer_model": args.writer_model,
            "judge_endpoint": args.judge_endpoint,
            "judge_model": args.judge_model,
            "seed": args.seed,
        }

    def _checkpoint_path(self, test_id: str, mode: str) -> Path:
        safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in test_id)
        return self.checkpoint_dir / f"{safe_id}--{mode}.json"

    @staticmethod
    def _write_checkpoint(path: Path, payload: Dict[str, Any]) -> None:
        temporary = path.with_suffix(f".{threading.get_ident()}.tmp")
        temporary.write_text(
            json.dumps(jsonable(payload), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    @staticmethod
    def _successful_call(calls: List[Dict[str, Any]], purpose: str) -> Dict[str, Any] | None:
        for call in reversed(calls):
            choices = (call.get("response") or {}).get("choices") or []
            finish_reason = choices[0].get("finish_reason") if choices else None
            if (
                call.get("purpose") == purpose
                and "response" in call
                and "error" not in call
                and finish_reason != "length"
            ):
                return call
        return None

    @staticmethod
    def _content_from_call(call: Dict[str, Any]) -> str:
        return call["response"]["choices"][0]["message"]["content"]

    def run_one(self, case: Dict[str, Any], mode: str) -> Dict[str, Any]:
        checkpoint_path = self._checkpoint_path(case["test_id"], mode)
        if checkpoint_path.exists():
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if checkpoint.get("signature") != self.checkpoint_signature:
                raise RuntimeError(
                    f"checkpoint signature mismatch for {case['test_id']} {mode}; "
                    "use a different --checkpoint-dir"
                )
        else:
            checkpoint = {
                "schema_version": "chapter3-memory-checkpoint-v1",
                "signature": self.checkpoint_signature,
                "test_id": case["test_id"],
                "mode": mode,
                "status": "running",
                "memory_states": [],
                "writer_calls": [],
                "judge_calls": [],
            }
        if checkpoint.get("status") == "completed" and checkpoint.get("result"):
            result = dict(checkpoint["result"])
            result["_receipts"] = checkpoint.get("writer_calls", []) + checkpoint.get("judge_calls", [])
            result["_resumed"] = True
            return result

        writer: ChatRecorder
        judge: ChatRecorder

        def persist_calls() -> None:
            checkpoint["writer_calls"] = writer.calls
            checkpoint["judge_calls"] = judge.calls
            checkpoint["updated_at_epoch"] = time.time()
            self._write_checkpoint(checkpoint_path, checkpoint)

        class JobRecorder(ChatRecorder):
            def create(inner_self, *, purpose: str, **request: Any) -> Any:
                try:
                    return super(JobRecorder, inner_self).create(purpose=purpose, **request)
                finally:
                    persist_calls()

        writer = JobRecorder(self.writer_client, "ark", self.args.writer_endpoint)
        judge = JobRecorder(self.judge_client, "moonshot", self.args.judge_endpoint)
        writer.calls = list(checkpoint.get("writer_calls", []))
        judge.calls = list(checkpoint.get("judge_calls", []))

        states = list(checkpoint.get("memory_states", []))
        memory: Any = states[-1]["memory"] if states else initial_memory(mode)
        for index, history in enumerate(case["conversation_histories"], start=1):
            if index <= len(states):
                continue
            messages = memory_prompt(mode, memory, history, index)
            purpose = f"3-1/3-2 memory update {case['test_id']} {mode} session {index}"
            prior_call = self._successful_call(writer.calls, purpose)
            if prior_call:
                content = self._content_from_call(prior_call)
            else:
                response = writer.create(
                    purpose=purpose,
                    model=self.args.writer_model,
                    messages=messages,
                    temperature=0,
                    seed=self.args.seed,
                    max_tokens=self.args.memory_max_tokens,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
            parsed = parse_json(content)
            memory = parsed.get("memory", parsed)
            states.append(
                {
                    "session_index": index,
                    "conversation_id": history.get("conversation_id"),
                    "memory": memory,
                    "isolation": {
                        "prior_raw_histories_supplied": 0,
                        "current_memory_supplied": True,
                        "new_history_supplied": history.get("conversation_id"),
                    },
                }
            )
            checkpoint["memory_states"] = states
            persist_calls()

        answer_purpose = f"3-1/3-2 answer {case['test_id']} {mode}"
        answer_call = self._successful_call(writer.calls, answer_purpose)
        if answer_call:
            answer = self._content_from_call(answer_call) or ""
        else:
            answer_response = writer.create(
                purpose=answer_purpose,
                model=self.args.writer_model,
                messages=answer_prompt(mode, memory, case["user_question"]),
                temperature=0,
                seed=self.args.seed,
                max_tokens=self.args.answer_max_tokens,
            )
            answer = answer_response.choices[0].message.content or ""
        checkpoint["answer"] = answer
        persist_calls()

        judge_purpose = f"3-1/3-2 independent judge {case['test_id']} {mode}"
        prior_judge = self._successful_call(judge.calls, judge_purpose)
        if prior_judge:
            judge_content = self._content_from_call(prior_judge)
        else:
            judge_response = judge.create(
                purpose=judge_purpose,
                model=self.args.judge_model,
                messages=judge_prompt(case, answer),
                temperature=0,
                seed=self.args.seed,
                max_tokens=self.args.judge_max_tokens,
                response_format={"type": "json_object"},
            )
            judge_content = judge_response.choices[0].message.content
        judge_raw = parse_json(judge_content)
        result = {
            "test_id": case["test_id"],
            "layer": case["category"],
            "title": case["title"],
            "mode": mode,
            "session_count": len(case["conversation_histories"]),
            "memory_states": states,
            "answer": answer,
            "judge": judge_summary(judge_raw),
            "judge_raw": judge_raw,
        }
        checkpoint["status"] = "completed"
        checkpoint["result"] = result
        persist_calls()
        result["_receipts"] = writer.calls + judge.calls
        result["_resumed"] = False
        return result


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    groups: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for result in results:
        groups[result["mode"]][result["layer"]].append(result)
    output: Dict[str, Any] = {}
    for mode, layers in groups.items():
        output[mode] = {}
        all_rows = []
        for layer, rows in sorted(layers.items()):
            all_rows.extend(rows)
            output[mode][layer] = {
                "n": len(rows),
                "pass_rate": sum(r["judge"]["passed"] for r in rows) / len(rows),
                "mean_reward": statistics.mean(r["judge"]["reward"] for r in rows),
                "hallucination_rate": sum(r["judge"]["hallucination_veto"] for r in rows) / len(rows),
            }
        output[mode]["overall"] = {
            "n": len(all_rows),
            "pass_rate": sum(r["judge"]["passed"] for r in all_rows) / len(all_rows),
            "mean_reward": statistics.mean(r["judge"]["reward"] for r in all_rows),
            "hallucination_rate": sum(r["judge"]["hallucination_veto"] for r in all_rows) / len(all_rows),
        }
    return output


def token_totals(calls: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for call in calls:
        usage = call.get("usage") or {}
        for key in totals:
            totals[key] += int(usage.get(key) or 0)
    return totals


def mode_call_stats(calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    output = {}
    for mode in MODES:
        selected = [call for call in calls if f" {mode}" in str(call.get("purpose", ""))]
        latencies = [float(call.get("latency_ms") or 0) for call in selected]
        output[mode] = {
            "api_calls": len(selected),
            "token_usage": token_totals(selected),
            "latency_ms": {
                "total": sum(latencies),
                "mean_per_call": statistics.mean(latencies) if latencies else 0,
            },
        }
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Live sequential memory comparison for Experiments 3-1/3-2")
    parser.add_argument("--all", action="store_true", help="run all 60 cases (authoritative campaign)")
    parser.add_argument("--case", action="append", help="run a specific test id (repeatable)")
    parser.add_argument("--per-layer", type=int, default=2, help="default smoke cases per layer")
    parser.add_argument("--mode", action="append", choices=MODES, help="memory mode (default: all four)")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--seed", type=int, default=37)
    parser.add_argument("--writer-model", default=os.getenv("ARK_MODEL", "doubao-seed-1-6-250615"))
    parser.add_argument("--judge-model", default=os.getenv("MEMORY_JUDGE_MODEL", "moonshot-v1-32k"))
    parser.add_argument("--writer-endpoint", default=ARK_ENDPOINT)
    parser.add_argument("--judge-endpoint", default=MOONSHOT_ENDPOINT)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--memory-max-tokens", type=int, default=6000)
    parser.add_argument("--answer-max-tokens", type=int, default=1200)
    parser.add_argument("--judge-max-tokens", type=int, default=1800)
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=HERE / "validation" / "checkpoints" / "full-60x4",
        help="per-case/mode resumable raw-call checkpoints",
    )
    parser.add_argument(
        "--test-cases-dir",
        type=Path,
        default=CHAPTER / "user-memory-evaluation" / "test_cases",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cases = load_cases(args.test_cases_dir.resolve(), args)
    modes = tuple(args.mode or MODES)
    expected_total = len(cases) * len(modes)
    print(f"Running {len(cases)} cases × {len(modes)} modes = {expected_total} evaluations")
    campaign = Campaign(args)
    results = []
    calls: List[Dict[str, Any]] = []
    errors = []
    jobs = [(case, mode) for case in cases for mode in modes]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_map = {pool.submit(campaign.run_one, case, mode): (case["test_id"], mode) for case, mode in jobs}
        for future in concurrent.futures.as_completed(future_map):
            test_id, mode = future_map[future]
            try:
                result = future.result()
                calls.extend(result.pop("_receipts", []))
                resumed = result.pop("_resumed", False)
                results.append(result)
                marker = "resumed" if resumed else "live"
                print(f"[{len(results)}/{expected_total}] {test_id} {mode}: reward={result['judge']['reward']:.3f} ({marker})")
            except Exception as exc:
                errors.append({"test_id": test_id, "mode": mode, "type": type(exc).__name__, "error": str(exc)})
                print(f"[ERROR] {test_id} {mode}: {exc}", file=sys.stderr)

    results.sort(key=lambda r: (r["test_id"], r["mode"]))
    full_suite = (
        len(cases) == 60
        and set(modes) == set(MODES)
        and len(results) == 240
        and not errors
    )
    status = "passed" if full_suite else ("partial" if results else "blocked")
    isolation_ok = all(
        state["isolation"]["prior_raw_histories_supplied"] == 0
        for result in results
        for state in result["memory_states"]
    )
    evidence = {
        "status": status,
        "scope": {
            "dataset_cases_available": len(list(args.test_cases_dir.glob("layer*/*.yaml"))),
            "cases_run": len(cases),
            "modes": list(modes),
            "evaluations_completed": len(results),
            "evaluations_expected": expected_total,
            "layers": sorted({c["category"] for c in cases}),
        },
        "configuration": {
            "writer_provider": "ark",
            "writer_endpoint": args.writer_endpoint,
            "writer_model": args.writer_model,
            "writer_seed": args.seed,
            "judge_provider": "moonshot",
            "judge_endpoint": args.judge_endpoint,
            "judge_model": args.judge_model,
            "judge_is_external_to_writer": True,
            "workers": args.workers,
            "memory_max_tokens": args.memory_max_tokens,
            "answer_max_tokens": args.answer_max_tokens,
            "judge_max_tokens": args.judge_max_tokens,
        },
        "acceptance": {
            "all_60_cases": len(cases) == 60,
            "twenty_per_layer": all(sum(c["category"] == layer for c in cases) == 20 for layer in ("layer1", "layer2", "layer3")),
            "all_four_modes": set(modes) == set(MODES),
            "sequential_memory_only": isolation_ok,
            "independent_llm_judge": True,
            "all_calls_succeeded": not errors,
            "passed": full_suite and isolation_ok,
        },
        "summary": {
            "aggregate": aggregate(results) if results else {},
            "token_usage": token_totals(calls),
            "by_mode": mode_call_stats(calls),
            "api_calls": len(calls),
            "errors": len(errors),
        },
        "errors": errors,
        "results": results,
    }
    manifest = write_campaign_evidence(
        HERE,
        "3-1-and-3-2",
        evidence,
        calls,
        input_paths=[HERE / "run_evaluation.py", *[c["_path"] for c in cases]],
    )
    print(json.dumps(manifest["summary"], ensure_ascii=False, indent=2))
    print(f"Canonical evidence: {HERE / 'validation' / 'latest.json'}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
