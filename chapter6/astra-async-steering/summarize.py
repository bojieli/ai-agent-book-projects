"""Recompute the experiment summary from verified wire evidence, without API calls."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

from experiment import digest, judge, replay, write_json


def summarize(run_dir):
    replay(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    groups = defaultdict(list)
    reasoning_windows = []
    for case in manifest["cases"]:
        rows = [json.loads(s) for s in (run_dir / case["name"] / "events.jsonl").read_text().splitlines()]
        result = judge(rows, case["arm"], case["model"])
        groups[case["arm"]].append(result)
        if case["arm"] == "steer_reasoning":
            steer = next(r for r in rows if r["event"].get("type") == "response.steer")
            opened = next(r for r in rows if r["event"].get("type") == "response.output_item.added"
                          and r["event"]["item"]["type"] == "reasoning")
            closed = next(r for r in rows if r["event"].get("type") == "response.output_item.done"
                          and r["event"]["item"]["id"] == opened["event"]["item"]["id"])
            reasoning_windows.append({"case": case["name"], "reasoning_open_s": opened["t_s"],
                "steer_sent_s": steer["t_s"], "reasoning_closed_s": closed["t_s"],
                "steer_inside_observed_reasoning_item": opened["index"] < steer["index"] < closed["index"]})
    summary = {"run": run_dir.name, "started_utc": manifest["started_utc"],
        "finished_utc": manifest["finished_utc"], "manifest_sha256": digest(run_dir / "manifest.json"),
        "summarizer_sha256": digest(Path(__file__)), "formal_cases": len(manifest["cases"]),
        "passed": sum(c["passed"] for c in manifest["cases"]), "groups": {},
        "reasoning_windows": reasoning_windows,
        "latency_scope": "Client-observed times; not server sampling latency or a statistical performance benchmark."}
    for arm, results in groups.items():
        metrics = [r["metrics"] for r in results]
        elapsed = [m["elapsed_s"] for m in metrics if "elapsed_s" in m]
        latency = [m["accepted_latency_s"] for m in metrics if m.get("accepted_latency_s") is not None]
        usage = [u for m in metrics for u in m.get("usage", []) if u]
        summary["groups"][arm] = {
            "cases": len(results), "passed": sum(r["passed"] for r in results),
            "models": sorted({model for m in metrics for model in m["returned_models"]}),
            "independent_output_before_tool_ready": sum(m.get("independent_text_while_tool_pending", False) for m in metrics),
            "automatic_successors": sum(m.get("automatic_successor", False) for m in metrics),
            "steered_incomplete_parents": sum(m.get("parent_incomplete_reason") == "steered" for m in metrics),
            "pending_notifications": sum(m["steer_pending"] for m in metrics),
            "median_elapsed_s": round(statistics.median(elapsed), 3) if elapsed else None,
            "ack_latency_range_s": [min(latency), max(latency)] if latency else None,
            "reported_input_tokens": sum(u["input_tokens"] for u in usage),
            "reported_output_tokens": sum(u["output_tokens"] for u in usage),
            "usage_available": bool(usage),
        }
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = summarize(args.run_dir)
    if args.out:
        write_json(args.out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
