#!/usr/bin/env python3
"""Run the pre-registered Experiment 10-1 comparison.

Within each paired cell both paths use the same model, task text, temperature and fresh conversation.
The script saves per-trial trajectories and the deterministic rubric results;
it does not claim a result until the requested trials have actually run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI

from demo import COMPOSITE_TASK
from evaluation import BOUNDARY_CASES, evaluate_boundary, evaluate_task
from orchestrator import MultiRoleOrchestrator
from roles import ROLES, transfer_tool_schema
from skill_orchestrator import (
    SkillOrchestrator,
    _fixed_system_prompt,
    load_skill,
    load_skill_tool_schema,
)
from tools import TOOL_SCHEMAS


TRANSFER_MECHANISM_PROMPT = (
    "\n\n【本路径的转换机制】需要切换专业能力时，调用 "
    "transfer_to_agent(target_role, reason)。角色规程中‘请求切换’均指这个工具。"
    "不要调用 load_skill；它在本路径中不可用。"
)


class ComparisonTransferOrchestrator(MultiRoleOrchestrator):
    """Transfer mechanics with the exact same canonical role documents as the Skill arm."""

    def _messages_for_api(self) -> list[dict]:
        system_prompt = load_skill(self.current_role) + TRANSFER_MECHANISM_PROMPT
        return [{"role": "system", "content": system_prompt}, *self.history]


def _canonical_hash(value: Any) -> str:
    body = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _static_prefix_hashes(path: str, api_calls: list[dict]) -> list[str]:
    """Hash the system+tools prefix as a mechanism proxy, not a cache claim."""
    hashes: list[str] = []
    if path == "skill":
        prefix = {
            "system": _fixed_system_prompt(),
            "tools": [*TOOL_SCHEMAS.values(), load_skill_tool_schema()],
        }
        return [_canonical_hash(prefix) for _ in api_calls]
    for call in api_calls:
        role_name = call.get("role")
        role = ROLES[role_name]
        tools = [TOOL_SCHEMAS[name] for name in role.tools]
        tools.append(transfer_tool_schema())
        system_prompt = load_skill(role_name) + TRANSFER_MECHANISM_PROMPT
        hashes.append(_canonical_hash({"system": system_prompt, "tools": tools}))
    return hashes


def _usage_totals(api_calls: list[dict]) -> dict:
    prompt = completion = cached = 0
    for call in api_calls:
        usage = call.get("usage") or {}
        prompt += int(usage.get("prompt_tokens", 0) or 0)
        completion += int(usage.get("completion_tokens", 0) or 0)
        details = usage.get("prompt_tokens_details") or {}
        cached += int(details.get("cached_tokens", 0) or 0)
    return {
        "input_tokens": prompt,
        "output_tokens": completion,
        "cached_input_tokens": cached,
        "uncached_input_tokens": max(prompt - cached, 0),
        "api_calls": len(api_calls),
    }


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _paired_bootstrap_interval(values: list[float], samples: int = 10_000) -> list[float] | None:
    if not values:
        return None
    rng = random.Random(102)
    means = [
        statistics.mean(rng.choice(values) for _ in values)
        for _ in range(samples)
    ]
    return [round(_percentile(means, 0.025) or 0.0, 6),
            round(_percentile(means, 0.975) or 0.0, 6)]


def _mcnemar_exact(transfer_pass: list[bool], skill_pass: list[bool]) -> dict:
    transfer_only = sum(a and not b for a, b in zip(transfer_pass, skill_pass))
    skill_only = sum(b and not a for a, b in zip(transfer_pass, skill_pass))
    discordant = transfer_only + skill_only
    if discordant == 0:
        p_value = 1.0
    else:
        tail = sum(math.comb(discordant, i) for i in range(min(transfer_only, skill_only) + 1))
        p_value = min(1.0, 2 * tail / (2 ** discordant))
    return {
        "transfer_only_passes": transfer_only,
        "skill_only_passes": skill_only,
        "discordant_pairs": discordant,
        "two_sided_exact_p": p_value,
    }


def _priced_cost(usage: dict, input_price: float | None, output_price: float | None,
                 cached_input_price: float | None) -> float | None:
    if input_price is None or output_price is None:
        return None
    uncached = usage["uncached_input_tokens"]
    cached = usage["cached_input_tokens"]
    cache_price = input_price if cached_input_price is None else cached_input_price
    return (uncached / 1_000_000 * input_price
            + cached / 1_000_000 * cache_price
            + usage["output_tokens"] / 1_000_000 * output_price)


def _contains_in_order(observed: list[str], required: list[str]) -> bool:
    cursor = 0
    for item in observed:
        if cursor < len(required) and item == required[cursor]:
            cursor += 1
    return cursor == len(required)


def _path_run(path: str, client: OpenAI, model: str, task: str, max_steps: int,
              kind: str = "cagr", task_spec: dict | None = None,
              max_output_tokens: int | None = None) -> dict:
    started = time.monotonic()
    provider_receipts: list[dict] = []
    tavily_receipts: list[dict] = []

    def record_provider(receipt: dict) -> None:
        provider_receipts.append(receipt)

    def record_tavily(receipt: dict) -> None:
        tavily_receipts.append(receipt)

    if path == "transfer":
        agent = ComparisonTransferOrchestrator(
            client=client, model=model, max_steps=max_steps,
            max_output_tokens=max_output_tokens, verbose=False,
            provider_receipt_sink=record_provider,
            tool_receipt_sink=record_tavily,
        )
    else:
        agent = SkillOrchestrator(
            client=client, model=model, max_steps=max_steps,
            max_output_tokens=max_output_tokens, verbose=False,
            provider_receipt_sink=record_provider,
            tool_receipt_sink=record_tavily,
        )
    final = agent.run(task)
    metrics = _usage_totals(agent.api_calls)
    prefix_hashes = _static_prefix_hashes(path, agent.api_calls)
    metrics.update({
        "static_prefix_hashes": prefix_hashes,
        "unique_static_prefixes": len(set(prefix_hashes)),
        "prefix_changed_calls": sum(left != right for left, right in zip(prefix_hashes, prefix_hashes[1:])),
        "cache_hit_rate": (
            metrics["cached_input_tokens"] / metrics["input_tokens"]
            if metrics["input_tokens"] else 0.0
        ),
    })
    payload = {
        "path": path,
        "final_answer": final,
        "history": agent.history,
        "api_calls": agent.api_calls,
        "metrics": metrics,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "terminated_by_limit": agent.terminated_by_limit,
        # Keep the raw provider/search boundaries beside every trajectory.  The
        # request bodies contain no API key (Tavily removes it before recording),
        # so a clean-clone reviewer can independently inspect each cell.
        "provider_receipts": provider_receipts,
        "tavily_receipts": tavily_receipts,
    }
    if path == "transfer":
        payload["handoff_chain"] = agent.handoff_chain_str()
        payload["transitions"] = [vars(item) for item in agent.handoffs]
        observed_capabilities = ["triage", *[item.to_role for item in agent.handoffs]]
    else:
        payload["loaded_skills"] = [item.name for item in agent.loaded_skills]
        payload["transitions"] = payload["loaded_skills"]
        observed_capabilities = payload["loaded_skills"]
        payload["skill_cache"] = {
            "hits": agent.skill_cache_hits,
            "misses": agent.skill_cache_misses,
            "load_latency_seconds": agent.skill_load_latency_seconds,
        }
    required_capabilities = {
        "cagr": ["triage", "research", "data_analysis", "writing"],
        "coding": ["triage", "coding", "writing"],
        "writing": ["triage", "writing"],
    }.get(kind, ["triage", "research", "data_analysis", "writing"])
    if task_spec and task_spec.get("required_capabilities"):
        required_capabilities = list(task_spec["required_capabilities"])
    payload["process"] = {
        "observed_capabilities": observed_capabilities,
        "required_capabilities": required_capabilities,
        "required_sequence_complete": _contains_in_order(
            observed_capabilities, required_capabilities
        ),
    }
    payload["task_kind"] = kind
    payload["task_spec"] = task_spec or {"kind": kind}
    payload["outcome"] = evaluate_task(final, agent.history, kind=kind, spec=task_spec)
    # A task is not accepted merely because the final text looks plausible: the
    # declared role/Skill sequence is itself a deterministic acceptance gate.
    payload["outcome"]["dimensions"]["required_capability_sequence"] = int(
        payload["process"]["required_sequence_complete"]
    )
    payload["outcome"]["pass"] = bool(
        payload["outcome"]["pass"]
        and payload["process"]["required_sequence_complete"]
    )
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"))
    parser.add_argument("--base-url", default=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    parser.add_argument("--api-key", default=None, help="默认读取 OPENAI_API_KEY")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--max-output-tokens", type=int, default=1200,
                        help="每次模型调用的输出上限；设为 0 使用服务商默认值")
    parser.add_argument("--request-timeout", type=float, default=120.0,
                        help="模型 HTTP 请求超时（秒）")
    parser.add_argument("--task", default=COMPOSITE_TASK)
    parser.add_argument("--task-file", type=Path,
                        help="JSON 数组；每项包含 id/prompt/kind，可附加可观察规则门禁")
    parser.add_argument("--skip-boundary", action="store_true")
    parser.add_argument("--replay", type=Path,
                        help="不调用 API；用当前评分器重放已有 comparison JSON")
    parser.add_argument("--output", type=Path,
                        default=Path("validation/comparison/latest.json"))
    parser.add_argument("--resume", type=Path,
                        help="从已有的部分 comparison JSON 继续；已完成的 pair/case 会跳过")
    parser.add_argument("--input-price-per-million", type=float, default=None)
    parser.add_argument("--cached-input-price-per-million", type=float, default=None)
    parser.add_argument("--output-price-per-million", type=float, default=None)
    return parser.parse_args()


def _rescore_run(run: dict) -> None:
    run["outcome"] = evaluate_task(
        run["final_answer"], run["history"], kind=run.get("task_kind", "cagr"),
        spec=run.get("task_spec")
    )
    if run["path"] == "transfer":
        observed = ["triage", *[item["to_role"] for item in run.get("transitions", [])]]
    else:
        observed = list(run.get("loaded_skills", []))
    required_by_kind = {
        "cagr": ["triage", "research", "data_analysis", "writing"],
        "coding": ["triage", "coding", "writing"],
        "writing": ["triage", "writing"],
    }
    required = (run.get("task_spec") or {}).get("required_capabilities")
    if not required:
        required = required_by_kind.get(run.get("task_kind", "cagr"), required_by_kind["cagr"])
    run["process"] = {
        "observed_capabilities": observed,
        "required_capabilities": required,
        "required_sequence_complete": _contains_in_order(observed, required),
    }
    run["outcome"].setdefault("dimensions", {})["required_capability_sequence"] = int(
        run["process"]["required_sequence_complete"]
    )
    run["outcome"]["pass"] = bool(
        run["outcome"]["pass"] and run["process"]["required_sequence_complete"]
    )


def _replay(args: argparse.Namespace) -> int:
    payload = json.loads(args.replay.read_text(encoding="utf-8"))
    for run in payload.get("runs", []):
        _rescore_run(run)
    for run in payload.get("boundary_runs", []):
        _rescore_run(run)
        case = next(item for item in BOUNDARY_CASES if item["id"] == run["case_id"])
        run["boundary"] = evaluate_boundary(run["final_answer"], run["history"], case)
    source_pricing = payload.get("pricing") or {}
    if args.input_price_per_million is None:
        args.input_price_per_million = source_pricing.get("input_per_million")
    if args.cached_input_price_per_million is None:
        args.cached_input_price_per_million = source_pricing.get("cached_input_per_million")
    if args.output_price_per_million is None:
        args.output_price_per_million = source_pricing.get("output_per_million")
    payload["aggregate"] = _aggregate(payload.get("runs", []), args)
    payload["paired_comparison"] = _paired_comparison(payload.get("runs", []), args)
    boundaries = payload.get("boundary_runs", [])
    payload["boundary_summary"] = {
        path: {
            "n": sum(item["path"] == path for item in boundaries),
            "pass_rate": (
                sum(item["path"] == path and item["boundary"]["pass"] for item in boundaries)
                / sum(item["path"] == path for item in boundaries)
                if any(item["path"] == path for item in boundaries) else None
            ),
        } for path in ("transfer", "skill")
    }
    payload["rescored_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload["evaluator_version"] = 2
    payload["max_steps"] = args.max_steps
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"rescored {args.replay} -> {args.output}")
    return 0


def _aggregate(runs: list[dict], args: argparse.Namespace) -> dict:
    grouped: dict[str, list[dict]] = {"transfer": [], "skill": []}
    for run in runs:
        grouped[run["path"]].append(run)
    result = {}
    for path, items in grouped.items():
        costs = [_priced_cost(item["metrics"], args.input_price_per_million,
                              args.output_price_per_million,
                              args.cached_input_price_per_million) for item in items]
        costs_known = [value for value in costs if value is not None]
        call_counts = [item["metrics"]["api_calls"] for item in items]
        uncached = [item["metrics"]["uncached_input_tokens"] for item in items]
        elapsed = [item["elapsed_seconds"] for item in items]
        cache_rates = [item["metrics"]["cache_hit_rate"] for item in items]
        passed = [bool(item["outcome"]["pass"]) for item in items]
        sequence_complete = [bool(item["process"]["required_sequence_complete"]) for item in items]
        result[path] = {
            "n": len(items),
            "pass_at_1": sum(passed) / len(passed) if passed else None,
            "pass_consecutive_k": all(passed),
            "required_role_sequence_rate": (
                sum(sequence_complete) / len(sequence_complete) if sequence_complete else None
            ),
            "cost_usd": {
                "mean": statistics.mean(costs_known) if costs_known else None,
                "p50": statistics.median(costs_known) if costs_known else None,
                "p95": _percentile(costs_known, 0.95),
            },
            "api_calls": {
                "mean": statistics.mean(call_counts) if call_counts else None,
                "p50": _percentile(call_counts, 0.5), "p95": _percentile(call_counts, 0.95),
            },
            "uncached_input_tokens": {
                "mean": statistics.mean(uncached) if uncached else None,
                "p50": _percentile(uncached, 0.5), "p95": _percentile(uncached, 0.95),
            },
            "elapsed_seconds": {
                "mean": statistics.mean(elapsed) if elapsed else None,
                "p50": _percentile(elapsed, 0.5), "p95": _percentile(elapsed, 0.95),
            },
            "cache_hit_rate": {"mean": statistics.mean(cache_rates) if cache_rates else None},
        }
        if path == "skill":
            result[path]["skill_document_cache"] = {
                "hits": sum(int(item.get("skill_cache", {}).get("hits", 0)) for item in items),
                "misses": sum(int(item.get("skill_cache", {}).get("misses", 0)) for item in items),
                "load_latency_p50": _percentile(
                    [latency for item in items for latency in item.get("skill_cache", {}).get("load_latency_seconds", [])],
                    0.5,
                ),
                "load_latency_p95": _percentile(
                    [latency for item in items for latency in item.get("skill_cache", {}).get("load_latency_seconds", [])],
                    0.95,
                ),
            }
    return result


def _paired_comparison(runs: list[dict], args: argparse.Namespace) -> dict:
    by_trial: dict[str, dict[str, dict]] = {}
    for item in runs:
        pair_id = str(item.get("pair_id", item["trial"]))
        by_trial.setdefault(pair_id, {})[item["path"]] = item
    pairs = [value for _, value in sorted(by_trial.items()) if set(value) == {"transfer", "skill"}]
    transfer_pass = [bool(pair["transfer"]["outcome"]["pass"]) for pair in pairs]
    skill_pass = [bool(pair["skill"]["outcome"]["pass"]) for pair in pairs]
    pass_delta = [float(b) - float(a) for a, b in zip(transfer_pass, skill_pass)]
    token_delta = [
        pair["skill"]["metrics"]["uncached_input_tokens"]
        - pair["transfer"]["metrics"]["uncached_input_tokens"] for pair in pairs
    ]
    latency_delta = [
        pair["skill"]["elapsed_seconds"] - pair["transfer"]["elapsed_seconds"]
        for pair in pairs
    ]
    result = {
        "difference_is_skill_minus_transfer": True,
        "paired_n": len(pairs),
        "pass_rate_delta": {
            "mean": statistics.mean(pass_delta) if pass_delta else None,
            "bootstrap_95_percent": _paired_bootstrap_interval(pass_delta),
        },
        "uncached_input_token_delta": {
            "median": statistics.median(token_delta) if token_delta else None,
            "bootstrap_mean_95_percent": _paired_bootstrap_interval(token_delta),
        },
        "latency_delta_seconds": {
            "median": statistics.median(latency_delta) if latency_delta else None,
            "bootstrap_mean_95_percent": _paired_bootstrap_interval(latency_delta),
        },
        "mcnemar": _mcnemar_exact(transfer_pass, skill_pass),
    }
    if args.input_price_per_million is not None and args.output_price_per_million is not None:
        cost_delta = []
        for pair in pairs:
            transfer_cost = _priced_cost(pair["transfer"]["metrics"], args.input_price_per_million,
                                         args.output_price_per_million,
                                         args.cached_input_price_per_million)
            skill_cost = _priced_cost(pair["skill"]["metrics"], args.input_price_per_million,
                                      args.output_price_per_million,
                                      args.cached_input_price_per_million)
            cost_delta.append(float(skill_cost) - float(transfer_cost))
        result["cost_delta_usd"] = {
            "median": statistics.median(cost_delta),
            "bootstrap_mean_95_percent": _paired_bootstrap_interval(cost_delta),
        }
    return result


def main(args: argparse.Namespace) -> int:
    if args.replay:
        return _replay(args)
    if args.trials < 1:
        raise SystemExit("--trials must be >= 1")
    api_key = args.api_key or os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("需要 OPENAI_API_KEY（或 OPENROUTER_API_KEY）才能进行 live comparison")
    base_url = args.base_url
    model = args.model
    if not (args.api_key or os.getenv("OPENAI_API_KEY")) and os.getenv("OPENROUTER_API_KEY"):
        base_url = "https://openrouter.ai/api/v1"
        if "/" not in model:
            model = f"openai/{model}" if model.startswith("gpt-") else model
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=args.request_timeout)
    max_output_tokens = args.max_output_tokens or None
    if args.task_file:
        task_specs = json.loads(args.task_file.read_text(encoding="utf-8"))
        if not isinstance(task_specs, list) or not task_specs:
            raise SystemExit("--task-file 必须是非空 JSON 数组")
        for index, item in enumerate(task_specs):
            if not isinstance(item, dict) or not isinstance(item.get("prompt"), str):
                raise SystemExit(f"--task-file 第 {index + 1} 项必须包含字符串 prompt")
            item.setdefault("id", f"task-{index + 1}")
            if item.get("kind", "cagr") not in {"cagr", "coding", "writing", "complex"}:
                raise SystemExit(f"--task-file 第 {index + 1} 项 kind 必须是 cagr/coding/writing/complex")
    else:
        task_specs = [{"id": "cagr", "prompt": args.task}]
    runs: list[dict] = []
    boundaries: list[dict] = []
    if args.resume:
        checkpoint = json.loads(args.resume.read_text(encoding="utf-8"))
        if checkpoint.get("experiment") != "10-1-role-switch-comparison":
            raise SystemExit("--resume 文件不是 Experiment 10-1 comparison")
        runs.extend(checkpoint.get("runs", []))
        boundaries.extend(checkpoint.get("boundary_runs", []))

    completed_cells = {
        (str(item.get("pair_id")), item.get("path")) for item in runs
    }
    completed_boundaries = {
        (str(item.get("case_id")), item.get("path")) for item in boundaries
    }

    def write_checkpoint() -> None:
        """Persist every completed cell so an interrupted live run is resumable."""
        args.output.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "schema_version": 1,
            "experiment": "10-1-role-switch-comparison",
            "checkpoint": True,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "base_url": base_url,
            "temperature": 0,
            "max_output_tokens": max_output_tokens,
            "request_timeout_seconds": args.request_timeout,
            "tasks": task_specs,
            "trials_per_task": args.trials,
            "paired_samples": len(task_specs) * args.trials,
            "pricing": {
                "input_per_million": args.input_price_per_million,
                "cached_input_per_million": args.cached_input_price_per_million,
                "output_per_million": args.output_price_per_million,
            },
            "runs": runs,
            "boundary_runs": boundaries,
        }
        temporary = args.output.with_suffix(args.output.suffix + ".tmp")
        temporary.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(args.output)

    for trial in range(1, args.trials + 1):
        for task_index, task_spec in enumerate(task_specs):
            path_order = (
                ("transfer", "skill") if (trial + task_index) % 2 else ("skill", "transfer")
            )
            for path in path_order:
                pair_id = f"{task_spec['id']}:{trial}"
                if (pair_id, path) in completed_cells:
                    continue
                run = _path_run(
                    path, client, model, task_spec["prompt"], args.max_steps,
                    str(task_spec.get("kind", "cagr")), task_spec,
                    max_output_tokens,
                )
                run["trial"] = trial
                run["task_id"] = str(task_spec["id"])
                run["pair_id"] = f"{task_spec['id']}:{trial}"
                runs.append(run)
                completed_cells.add((pair_id, path))
                write_checkpoint()
                print(f"task={task_spec['id']} trial={trial} path={path} "
                      f"pass={run['outcome']['pass']} calls={run['metrics']['api_calls']} "
                      f"input={run['metrics']['input_tokens']} output={run['metrics']['output_tokens']}")

    if not args.skip_boundary:
        for case in BOUNDARY_CASES:
            for path in ("transfer", "skill"):
                if (str(case["id"]), path) in completed_boundaries:
                    continue
                run = _path_run(
                    path, client, model, case["prompt"], args.max_steps,
                    max_output_tokens=max_output_tokens,
                )
                run["case_id"] = case["id"]
                run["boundary"] = evaluate_boundary(run["final_answer"], run["history"], case)
                # Do not duplicate full boundary histories in the summary; they are
                # retained in the per-run record so failures remain auditable.
                boundaries.append(run)
                completed_boundaries.add((str(case["id"]), path))
                write_checkpoint()
                print(f"boundary={case['id']} path={path} pass={run['boundary']['pass']}")

    payload: dict[str, Any] = {
        "schema_version": 1,
        "experiment": "10-1-role-switch-comparison",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "base_url": base_url,
        "temperature": 0,
        "max_output_tokens": max_output_tokens,
        "request_timeout_seconds": args.request_timeout,
        "tasks": task_specs,
        "trials_per_task": args.trials,
        "paired_samples": len(task_specs) * args.trials,
        "pricing": {
            "input_per_million": args.input_price_per_million,
            "cached_input_per_million": args.cached_input_price_per_million,
            "output_per_million": args.output_price_per_million,
        },
        "aggregate": _aggregate(runs, args),
        "paired_comparison": _paired_comparison(runs, args),
        "runs": runs,
        "boundary_runs": boundaries,
        "boundary_summary": {
            path: {
                "n": sum(item["path"] == path for item in boundaries),
                "pass_rate": (
                    sum(item["path"] == path and item["boundary"]["pass"] for item in boundaries)
                    / sum(item["path"] == path for item in boundaries)
                    if any(item["path"] == path for item in boundaries) else None
                ),
            } for path in ("transfer", "skill")
        },
        "protocol_note": (
            "Interpret results only with paired confidence intervals and a pre-registered task set; "
            "a single successful run is not evidence of superiority."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"saved {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(parse_args()))
