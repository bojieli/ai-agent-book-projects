#!/usr/bin/env python3
"""Run Experiment 1-3 on the exact GPT-5.6 Responses API surface."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from agent import GPT5NativeAgent
from config import Config


ASEAN_TASK = """Research the current official capitals and reliable coordinates
for the ten ASEAN member states. You must use hosted web search and cite the
sources. Then you must use the hosted Python tool—not mental arithmetic—to
enumerate all 45 capital pairs with the haversine formula and identify the
closest pair and distance. Include the coordinates, formula assumptions,
calculation result, retrieval date, and clickable citations. Do not say Python
was used unless a code_interpreter_call completes."""

AMBIGUOUS_TASK = "搜索最近一个月的比特币走势，做技术分析。"
CLARIFICATION_REPLY = (
    "使用 CoinGecko 的 BTC/USD 日线收盘价；分析 MA7、MA20、RSI14、MACD(12,26,9)、"
    "区间收益和最大回撤。请搜索数据并用托管 Python 工具实际计算，再给出含来源的报告。"
)


def git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def output_types(result: Dict[str, Any]) -> List[str]:
    return [item.get("type") for item in result.get("output_items") or []]


def completed_calls(result: Dict[str, Any], kind: str) -> List[Dict[str, Any]]:
    return [
        item
        for item in result.get("output_items") or []
        if item.get("type") == kind and item.get("status") == "completed"
    ]


def url_citations(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        item for item in result.get("citations") or [] if item.get("type") == "url_citation"
    ]


def exact_model(result: Dict[str, Any]) -> bool:
    requested = (result.get("requested_model") or result.get("model") or "").removeprefix(
        "openai/"
    )
    returned = (result.get("model") or "").removeprefix("openai/")
    return requested == "gpt-5.6-sol" and returned == "gpt-5.6-sol"


def validate_asean(result: Dict[str, Any]) -> Dict[str, Any]:
    answer = result.get("response") or ""
    checks = {
        "request_succeeded": result.get("success") is True,
        "exact_gpt_5_6_sol": exact_model(result),
        "web_search_completed": bool(completed_calls(result, "web_search_call")),
        "code_interpreter_completed": bool(
            completed_calls(result, "code_interpreter_call")
        ),
        "url_citations_present": len(url_citations(result)) >= 2,
        "closest_pair_reported": (
            "singapore" in answer.lower() or "新加坡" in answer
        )
        and ("kuala lumpur" in answer.lower() or "吉隆坡" in answer),
        "distance_reported": any(unit in answer.lower() for unit in ("km", "公里", "千米")),
    }
    return {"checks": checks, "passed": all(checks.values()), "output_types": output_types(result)}


def is_clarifying_question(result: Dict[str, Any]) -> bool:
    text = result.get("response") or ""
    return result.get("success") is True and not result.get("tool_calls") and (
        "?" in text or "？" in text
    )


def validate_clarification(
    first: Dict[str, Any], second: Dict[str, Any] | None
) -> Dict[str, Any]:
    checks = {
        "first_turn_clarified_before_tools": is_clarifying_question(first),
        "continuation_used_previous_response_id": bool(
            second and second.get("request", {}).get("previous_response_id") == first.get("response_id")
        ),
        "followup_succeeded": bool(second and second.get("success")),
        "followup_web_search_completed": bool(
            second and completed_calls(second, "web_search_call")
        ),
        "followup_code_interpreter_completed": bool(
            second and completed_calls(second, "code_interpreter_call")
        ),
        "followup_citations_present": bool(second and url_citations(second)),
    }
    return {"checks": checks, "passed": all(checks.values())}


def total_usage(results: Iterable[Dict[str, Any] | None]) -> Dict[str, Any]:
    totals: Dict[str, float] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "reported_cost_usd": 0.0,
    }
    cost_reported = False
    for result in results:
        usage = (result or {}).get("usage") or {}
        for name in ("input_tokens", "output_tokens", "total_tokens"):
            totals[name] += int(usage.get(name) or 0)
        if usage.get("cost") is not None:
            cost_reported = True
            totals["reported_cost_usd"] += float(usage["cost"])
    totals["reported_cost_available"] = cost_reported
    if not cost_reported:
        totals["reported_cost_usd"] = None
    return totals


def run_backend(backend: str, reasoning: str) -> Dict[str, Any]:
    key, base_url, model = Config.resolve(backend, "gpt-5.6-sol")
    if not key:
        return {"backend": backend, "started": False, "error": "credential_missing"}

    asean_agent = GPT5NativeAgent(key, base_url=base_url, model=model)
    asean = asean_agent.process_request(
        ASEAN_TASK,
        reasoning_effort=reasoning,
        verbosity="high",
        max_tokens=16000,
    )

    clarification_agent = GPT5NativeAgent(key, base_url=base_url, model=model)
    first = clarification_agent.process_request(
        AMBIGUOUS_TASK,
        reasoning_effort="medium",
        verbosity="medium",
        max_tokens=4000,
    )
    second = None
    if is_clarifying_question(first):
        second = clarification_agent.process_request(
            CLARIFICATION_REPLY,
            reasoning_effort=reasoning,
            verbosity="high",
            max_tokens=16000,
        )

    return {
        "backend": backend,
        "started": True,
        "base_url": base_url,
        "requested_model": model,
        "asean": asean,
        "asean_validation": validate_asean(asean),
        "clarification": {
            "ambiguous_task": AMBIGUOUS_TASK,
            "first": first,
            "user_reply": CLARIFICATION_REPLY if second else None,
            "second": second,
            "validation": validate_clarification(first, second),
        },
        "api_turns": asean_agent.api_turns + clarification_agent.api_turns,
        "usage": total_usage((asean, first, second)),
    }


def acceptance(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    official = next((run for run in runs if run.get("backend") == "openai"), {})
    proxy = next((run for run in runs if run.get("backend") == "openrouter"), {})
    checks = {
        "official_openai_asean_passed": official.get("asean_validation", {}).get("passed") is True,
        "official_openai_clarification_passed": official.get("clarification", {})
        .get("validation", {})
        .get("passed")
        is True,
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "openrouter_is_diagnostic_not_official_acceptance": bool(proxy),
        "official_docs": [
            "https://developers.openai.com/api/docs/models/gpt-5.6-sol",
            "https://developers.openai.com/api/docs/guides/tools-web-search",
            "https://developers.openai.com/api/docs/guides/tools-code-interpreter",
            "https://developers.openai.com/api/docs/guides/model-guidance?model=gpt-5.6-sol",
        ],
    }


def write_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backends", nargs="+", choices=["openai", "openrouter"], default=["openai", "openrouter"]
    )
    parser.add_argument(
        "--reasoning", choices=["low", "medium", "high", "xhigh", "max"], default="high"
    )
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    runs = [run_backend(backend, args.reasoning) for backend in args.backends]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path("validation") / f"real_{stamp}"
    evidence = {
        "schema_version": "1.0",
        "experiment_id": "1-3",
        "evidence_mode": "real_api",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_source": "book/chapter1.md#实验-1-3-gpt-5-6-原生-deep-research-能力",
        "host": {
            "platform": platform.platform(),
            "python": sys.version,
            "machine": platform.machine(),
        },
        "repository": {
            "commit": git_value("rev-parse", "HEAD"),
            "branch": git_value("branch", "--show-current"),
            "worktree_dirty": bool(git_value("status", "--porcelain")),
        },
        "credentials_recorded": False,
        "runs": runs,
    }
    evidence["acceptance"] = acceptance(runs)
    path = output_dir / "evidence.json"
    write_json(path, evidence)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (output_dir / "evidence.sha256").write_text(f"{digest}  evidence.json\n", encoding="utf-8")
    Path("validation").mkdir(exist_ok=True)
    shutil.copyfile(path, Path("validation/latest.json"))
    print(json.dumps(evidence["acceptance"], ensure_ascii=False, indent=2))
    print(f"Evidence: {path}")
    return 0 if evidence["acceptance"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
