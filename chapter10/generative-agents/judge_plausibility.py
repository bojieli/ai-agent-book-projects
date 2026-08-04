#!/usr/bin/env python3
"""Run arm-blind Anthropic plausibility judgments for baseline vs ablation."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


MODEL = "claude-sonnet-4-5-20250929"
DIMENSIONS = (
    "temporal_coherence",
    "personality_consistency",
    "memory_continuity",
    "social_responsiveness",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def evenly_sample(rows: list[Any], maximum: int) -> list[Any]:
    if len(rows) <= maximum:
        return rows
    if maximum == 1:
        return [rows[0]]
    indexes = {
        round(index * (len(rows) - 1) / (maximum - 1)) for index in range(maximum)
    }
    return [rows[index] for index in sorted(indexes)]


def seed_node_counts(output: Path) -> dict[str, int]:
    seed = output / "storage" / "exp10_7_history_seed" / "personas"
    result = {}
    for persona in seed.iterdir():
        if persona.is_dir():
            nodes = load_json(
                persona
                / "bootstrap_memory"
                / "associative_memory"
                / "nodes.json"
            )
            result[persona.name] = len(nodes)
    return result


def build_trace(output: Path, arm: str, persona: str, seed_count: int) -> dict:
    status = load_json(output / "status" / f"{arm}.json")
    sim = output / "storage" / status["current_sim"]
    scratch = load_json(
        sim / "personas" / persona / "bootstrap_memory" / "scratch.json"
    )
    nodes = load_json(
        sim
        / "personas"
        / persona
        / "bootstrap_memory"
        / "associative_memory"
        / "nodes.json"
    )
    new_memories = [
        {
            "created": row.get("created"),
            "type": row.get("type"),
            "depth": row.get("depth"),
            "description": row.get("description"),
            "evidence_count": len(row.get("filling") or []),
        }
        for row in nodes.values()
        if int(row.get("node_count", 0)) > seed_count
    ]
    transitions = []
    previous = None
    meta = load_json(sim / "reverie" / "meta.json")
    for step in range(int(meta["step"])):
        movement = load_json(sim / "movement" / f"{step}.json")
        description = str(movement["persona"][persona].get("description", ""))
        if description != previous:
            transitions.append(
                {
                    "time": movement["meta"]["curr_time"],
                    "action": description,
                }
            )
            previous = description
    return {
        "profile": {
            "name": scratch.get("name"),
            "innate_traits": scratch.get("innate"),
            "learned_traits": scratch.get("learned"),
            "initial_or_current_goal": scratch.get("currently"),
            "lifestyle": scratch.get("lifestyle"),
            "daily_plan_requirement": scratch.get("daily_plan_req"),
        },
        "action_transitions": evenly_sample(transitions, 40),
        "memory_stream_sample": evenly_sample(new_memories, 32),
        "counts": {
            "action_transitions": len(transitions),
            "new_memories": len(new_memories),
            "new_thoughts": sum(row["type"] == "thought" for row in new_memories),
            "evidence_linked_thoughts": sum(
                row["type"] == "thought" and row["evidence_count"] > 0
                for row in new_memories
            ),
        },
    }


def make_prompt(persona: str, trace_a: dict, trace_b: dict) -> str:
    rubric = {
        "temporal_coherence": "Actions form a feasible, non-contradictory two-day sequence.",
        "personality_consistency": "Actions remain consistent with the supplied traits, lifestyle, and goals.",
        "memory_continuity": "Later memories/actions coherently use earlier experiences instead of behaving as disconnected episodes.",
        "social_responsiveness": "The persona reacts coherently to other people and social information when such opportunities appear; do not penalize a trace merely for having few encounters.",
    }
    schema = {
        "A": {dimension: 1 for dimension in DIMENSIONS},
        "B": {dimension: 1 for dimension in DIMENSIONS},
        "preferred": "A, B, or tie",
        "evidence": {
            dimension: ["specific detail from A", "specific detail from B"]
            for dimension in DIMENSIONS
        },
        "confidence": "low, medium, or high",
    }
    return (
        "You are evaluating two unlabeled traces from the same simulated persona. "
        "Score each trace independently from 1 (implausible) to 5 (highly plausible). "
        "Judge only the supplied evidence. Do not infer which system produced a trace, "
        "do not reward verbosity or memory count by itself, and do not assume the expected winner.\n\n"
        f"Persona: {persona}\nRubric:\n{json.dumps(rubric, indent=2)}\n\n"
        f"Trace A:\n{json.dumps(trace_a, ensure_ascii=False)}\n\n"
        f"Trace B:\n{json.dumps(trace_b, ensure_ascii=False)}\n\n"
        "Return exactly one JSON object matching this shape, with integer scores from 1 to 5:\n"
        f"{json.dumps(schema, indent=2)}"
    )


def parse_json_object(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("response did not contain a JSON object")
    value = json.loads(text[start : end + 1])
    for label in ("A", "B"):
        for dimension in DIMENSIONS:
            score = value[label][dimension]
            if not isinstance(score, int) or not 1 <= score <= 5:
                raise ValueError(f"invalid {label} {dimension} score: {score!r}")
    if value.get("preferred") not in {"A", "B", "tie"}:
        raise ValueError("invalid preferred label")
    return value


def call_anthropic(prompt: str, api_key: str, model: str) -> tuple[dict, dict, float]:
    request_body = {
        "model": model,
        "max_tokens": 1800,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic HTTP {exc.code}: {body[:500]}") from exc
    latency = time.perf_counter() - started
    text = "".join(
        block.get("text", "") for block in raw.get("content", []) if block.get("type") == "text"
    )
    return request_body, raw, latency


def load_canonical_judgments(receipts_path: Path) -> list[dict]:
    """Keep failed judge attempts as evidence without polluting canonical rows."""

    if not receipts_path.exists():
        return []
    rows = [json.loads(line) for line in receipts_path.read_text().splitlines() if line]
    failed = [row for row in rows if not row.get("success")]
    if not failed:
        return rows
    failed_path = receipts_path.with_name(
        f"{receipts_path.stem}.failed-{time.time_ns()}{receipts_path.suffix}"
    )
    failed_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in failed),
        encoding="utf-8",
    )
    successful = [row for row in rows if row.get("success")]
    receipts_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in successful),
        encoding="utf-8",
    )
    return successful


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    output = args.output.resolve()
    api_key = os.environ["ANTHROPIC_API_KEY"]
    counts = seed_node_counts(output)
    personas = sorted(counts)
    if args.limit is not None:
        personas = personas[: args.limit]
    analysis = output / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    receipts_path = analysis / "plausibility_judgments.jsonl"
    rows = load_canonical_judgments(receipts_path)
    completed = {row["persona"] for row in rows}
    for persona in personas:
        if persona in completed:
            continue
        baseline = build_trace(output, "baseline", persona, counts[persona])
        ablation = build_trace(output, "no_reflection", persona, counts[persona])
        baseline_is_a = hashlib.sha256(persona.encode()).digest()[0] % 2 == 0
        trace_a, trace_b = (baseline, ablation) if baseline_is_a else (ablation, baseline)
        prompt = make_prompt(persona, trace_a, trace_b)
        try:
            request_body, response, latency = call_anthropic(prompt, api_key, args.model)
            text = "".join(
                block.get("text", "")
                for block in response.get("content", [])
                if block.get("type") == "text"
            )
            judgment = parse_json_object(text)
            row = {
                "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "persona": persona,
                "baseline_label": "A" if baseline_is_a else "B",
                "request": request_body,
                "response": response,
                "latency_seconds": round(latency, 3),
                "judgment": judgment,
                "success": True,
                "error": None,
            }
        except Exception as exc:
            row = {
                "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "persona": persona,
                "baseline_label": "A" if baseline_is_a else "B",
                "request": {"model": args.model, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()},
                "response": None,
                "latency_seconds": None,
                "judgment": None,
                "success": False,
                "error": {"type": type(exc).__name__, "message": str(exc)[:1000]},
            }
        if not row["success"]:
            failed_path = receipts_path.with_name(
                f"{receipts_path.stem}.failed-{time.time_ns()}{receipts_path.suffix}"
            )
            failed_path.write_text(
                json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            raise RuntimeError(row["error"])
        with receipts_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        rows.append(row)

    successful = [row for row in rows if row.get("success") and row["persona"] in personas]
    paired = {dimension: {"baseline": [], "no_reflection": []} for dimension in DIMENSIONS}
    preferences = {"baseline": 0, "no_reflection": 0, "tie": 0}
    for row in successful:
        baseline_label = row["baseline_label"]
        ablation_label = "B" if baseline_label == "A" else "A"
        for dimension in DIMENSIONS:
            paired[dimension]["baseline"].append(row["judgment"][baseline_label][dimension])
            paired[dimension]["no_reflection"].append(row["judgment"][ablation_label][dimension])
        preferred = row["judgment"]["preferred"]
        if preferred == "tie":
            preferences["tie"] += 1
        elif preferred == baseline_label:
            preferences["baseline"] += 1
        else:
            preferences["no_reflection"] += 1
    summary = {
        "schema_version": 1,
        "experiment": "10-7",
        "model": args.model,
        "judgments": len(successful),
        "preferences": preferences,
        "mean_scores": {
            dimension: {
                arm: statistics.mean(values) if values else None
                for arm, values in arms.items()
            }
            for dimension, arms in paired.items()
        },
        "raw_receipts": str(receipts_path.relative_to(output)),
    }
    (analysis / "plausibility_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
