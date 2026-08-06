#!/usr/bin/env python3
"""Analyze memory, reflection, diffusion, and action logs for Experiment 10-7."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import statistics
from pathlib import Path
from typing import Any, Iterable


ARMS = ("baseline", "custom_goal", "no_reflection")
EVENT_TERMS = {
    "baseline": ("valentine", "party"),
    "custom_goal": ("climate", "resilience", "workshop"),
    "no_reflection": ("valentine", "party"),
}
ELECTION_TERMS = ("mayor", "election")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def persona_nodes(sim_dir: Path) -> dict[str, list[dict[str, Any]]]:
    result = {}
    personas_dir = sim_dir / "personas"
    for persona_dir in sorted(path for path in personas_dir.iterdir() if path.is_dir()):
        path = (
            persona_dir
            / "bootstrap_memory"
            / "associative_memory"
            / "nodes.json"
        )
        nodes = load_json(path)
        result[persona_dir.name] = list(nodes.values())
    return result


def contains_terms(node: dict[str, Any], terms: Iterable[str]) -> bool:
    text = " ".join(
        str(node.get(key, ""))
        for key in ("subject", "predicate", "object", "description", "embedding_key")
    ).lower()
    return any(term in text for term in terms)


def diffusion(nodes: dict[str, list[dict[str, Any]]], terms: tuple[str, ...]) -> dict:
    aware = {}
    mentions = {}
    for name, rows in nodes.items():
        matching = [row for row in rows if contains_terms(row, terms)]
        if matching:
            created = sorted(row.get("created") for row in matching if row.get("created"))
            aware[name] = created[0] if created else None
            mentions[name] = len(matching)
    return {
        "terms": list(terms),
        "aware_agents": len(aware),
        "first_mention_by_agent": aware,
        "memory_mentions_by_agent": mentions,
    }


def memory_summary(
    nodes: dict[str, list[dict[str, Any]]], seed_counts: dict[str, int]
) -> dict:
    totals = collections.Counter()
    new_totals = collections.Counter()
    new_by_persona = {}
    reflection_evidence = 0
    max_depth = 0
    chat_edges = collections.Counter()
    for name, rows in nodes.items():
        cutoff = seed_counts[name]
        new_rows = [row for row in rows if int(row.get("node_count", 0)) > cutoff]
        counts = collections.Counter(row.get("type", "unknown") for row in rows)
        new_counts = collections.Counter(row.get("type", "unknown") for row in new_rows)
        totals.update(counts)
        new_totals.update(new_counts)
        new_by_persona[name] = dict(new_counts)
        reflection_evidence += sum(
            row.get("type") == "thought" and bool(row.get("filling"))
            for row in new_rows
        )
        max_depth = max(max_depth, *(int(row.get("depth", 0)) for row in rows))
        for row in new_rows:
            if row.get("type") != "chat":
                continue
            subject = str(row.get("subject", ""))
            obj = str(row.get("object", ""))
            if subject and obj:
                chat_edges[tuple(sorted((subject, obj)))] += 1
    return {
        "all_nodes_by_type": dict(totals),
        "new_nodes_by_type": dict(new_totals),
        "new_nodes_by_persona": new_by_persona,
        "new_thoughts_with_evidence": reflection_evidence,
        "maximum_thought_depth": max_depth,
        "unique_chat_edges": len(chat_edges),
        "chat_nodes_by_edge": {
            " | ".join(edge): count for edge, count in sorted(chat_edges.items())
        },
    }


def action_summary(sim_dir: Path) -> dict:
    meta = load_json(sim_dir / "reverie" / "meta.json")
    descriptions: dict[str, list[str]] = {
        name: [] for name in meta["persona_names"]
    }
    transitions = collections.Counter()
    cafe_window: dict[str, set[str]] = collections.defaultdict(set)
    sample_steps = 0
    for step in range(int(meta["step"])):
        path = sim_dir / "movement" / f"{step}.json"
        movement = load_json(path)
        current = dt.datetime.strptime(
            movement["meta"]["curr_time"], "%B %d, %Y, %H:%M:%S"
        )
        in_event_window = (
            current.date() == dt.date(2023, 2, 14)
            and dt.time(17, 0) <= current.time() < dt.time(19, 0)
        )
        for name, row in movement["persona"].items():
            description = str(row.get("description", ""))
            descriptions[name].append(description)
            if in_event_window and "hobbs cafe" in description.lower():
                cafe_window[name].add(description)
        sample_steps += 1
    per_persona = {}
    for name, rows in descriptions.items():
        changes = sum(left != right for left, right in zip(rows, rows[1:]))
        transitions[name] = changes
        per_persona[name] = {
            "unique_descriptions": len(set(rows)),
            "description_changes": changes,
            "hobbs_cafe_event_window_descriptions": sorted(cafe_window.get(name, set())),
        }
    unique_counts = [row["unique_descriptions"] for row in per_persona.values()]
    change_counts = [row["description_changes"] for row in per_persona.values()]
    return {
        "steps": sample_steps,
        "persona_action_summary": per_persona,
        "hobbs_cafe_event_window_agents": sorted(cafe_window),
        "hobbs_cafe_event_window_agent_count": len(cafe_window),
        "median_unique_descriptions": statistics.median(unique_counts),
        "median_description_changes": statistics.median(change_counts),
    }


def provider_summary(status: dict) -> dict:
    calls = errors = transport_retries = 0
    usage = collections.Counter()
    latency = wall = 0.0
    for checkpoint in status.get("checkpoints", []):
        receipt = checkpoint["receipt_summary"]
        calls += int(receipt.get("calls", 0))
        errors += int(receipt.get("errors", 0))
        transport_retries += int(receipt.get("transport_retries", 0))
        usage.update(receipt.get("usage", {}))
        latency += float(receipt.get("provider_latency_seconds", 0))
        wall += float(checkpoint.get("wall_seconds", 0))
    return {
        "calls": calls,
        "errors": errors,
        "transport_retries": transport_retries,
        "usage": dict(usage),
        "provider_latency_seconds": round(latency, 3),
        "checkpoint_wall_seconds": round(wall, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    storage = output / "storage"
    seed_nodes = persona_nodes(storage / "exp10_7_history_seed")
    seed_counts = {name: len(rows) for name, rows in seed_nodes.items()}
    result = {
        "schema_version": 1,
        "experiment": "10-7",
        "source_commit": "fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4",
        "seed_memory_nodes_by_persona": seed_counts,
        "arms": {},
    }
    for arm in ARMS:
        status = load_json(output / "status" / f"{arm}.json")
        if not status.get("complete"):
            raise SystemExit(f"arm is incomplete: {arm}")
        sim_dir = storage / status["current_sim"]
        meta = load_json(sim_dir / "reverie" / "meta.json")
        nodes = persona_nodes(sim_dir)
        result["arms"][arm] = {
            "simulation": {
                "sim_code": status["current_sim"],
                "personas": len(meta["persona_names"]),
                "steps": meta["step"],
                "current_time": meta["curr_time"],
                "sec_per_step": meta["sec_per_step"],
            },
            "provider": provider_summary(status),
            "memory": memory_summary(nodes, seed_counts),
            "seeded_event_diffusion": diffusion(nodes, EVENT_TERMS[arm]),
            "election_diffusion": diffusion(nodes, ELECTION_TERMS),
            "actions": action_summary(sim_dir),
        }
    analysis_dir = output / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    path = analysis_dir / "deterministic_analysis.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
