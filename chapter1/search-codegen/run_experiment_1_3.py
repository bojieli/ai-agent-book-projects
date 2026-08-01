#!/usr/bin/env python3
"""Run Experiment 1-3 on a hosted web-search + code-execution Responses API.

Acceptance policy (author-mandated, 2026-07-31): the experiment's essence is
model-directed multi-round web search + hosted code execution, clarification
before tools, and a current answer with authoritative sources. The canonical
OpenAI GPT-5.6 Sol path remains the reference implementation, but acceptance
is NOT gated on the official OpenAI account: any provider whose Responses API
genuinely closes the search/code loop server-side (currently Alibaba Model
Studio DashScope ``qwen3.7-plus``) is an eligible acceptance backend. The
OpenRouter route stays a diagnostic and is never accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

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
    "区间收益和最大回撤，如代码环境支持请绘制收盘价走势图。请搜索数据并用托管 "
    "Python 工具实际计算，再给出含来源的报告和交易建议。"
)

# Backends whose runs may close the experiment, in priority order. The
# OpenRouter proxy is diagnostic-only and never appears here.
ACCEPTANCE_BACKENDS = ("openai", "dashscope")

# Independent reference: standard coordinates of the ten ASEAN capitals,
# used to verify the model's computed nearest pair without trusting it.
ASEAN_CAPITAL_COORDS: Dict[str, Tuple[float, float]] = {
    "Bandar Seri Begawan": (4.9031, 114.9398),
    "Phnom Penh": (11.5564, 104.9282),
    "Jakarta": (-6.2088, 106.8456),
    "Vientiane": (17.9757, 102.6331),
    "Kuala Lumpur": (3.1390, 101.6869),
    "Naypyidaw": (19.7633, 96.0785),
    "Manila": (14.5995, 120.9842),
    "Singapore": (1.3521, 103.8198),
    "Bangkok": (13.7563, 100.5018),
    "Hanoi": (21.0278, 105.8342),
}


def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    radius = 6371.0088
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(h))


def independent_asean_reference() -> Dict[str, Any]:
    """Locally computed ground truth for the ASEAN nearest-pair check."""
    pairs = [
        (haversine_km(ca, cb), a, b)
        for (a, ca), (b, cb) in itertools.combinations(ASEAN_CAPITAL_COORDS.items(), 2)
    ]
    distance, first, second = min(pairs)
    return {
        "pair": sorted([first, second]),
        "distance_km": round(distance, 1),
        "pair_count": len(pairs),
        "coordinates": ASEAN_CAPITAL_COORDS,
    }


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


def model_identity_exact(result: Dict[str, Any]) -> bool:
    """The returned model must be exactly the requested model."""
    requested = (result.get("requested_model") or result.get("model") or "").removeprefix(
        "openai/"
    )
    returned = (result.get("model") or "").removeprefix("openai/")
    return bool(requested) and requested == returned


def validate_asean(
    result: Dict[str, Any], reference: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    answer = result.get("response") or ""
    reference = reference or independent_asean_reference()
    pair_city, other_city = reference["pair"]
    checks = {
        "request_succeeded": result.get("success") is True,
        "model_identity_exact": model_identity_exact(result),
        "web_search_completed": bool(completed_calls(result, "web_search_call")),
        "code_interpreter_completed": bool(
            completed_calls(result, "code_interpreter_call")
        ),
        "url_citations_present": len(url_citations(result)) >= 2,
        "closest_pair_matches_independent_reference": (
            pair_city.lower() in answer.lower() and other_city.lower() in answer.lower()
        ),
        "distance_reported": any(unit in answer.lower() for unit in ("km", "公里", "千米")),
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "output_types": output_types(result),
        "independent_reference": {
            "pair": reference["pair"],
            "distance_km": reference["distance_km"],
            "pair_count": reference["pair_count"],
        },
    }


def is_clarifying_question(result: Dict[str, Any]) -> bool:
    text = result.get("response") or ""
    return result.get("success") is True and not result.get("tool_calls") and (
        "?" in text or "？" in text
    )


def validate_clarification(
    first: Dict[str, Any], second: Dict[str, Any] | None
) -> Dict[str, Any]:
    followup_text = (second or {}).get("response") or ""
    lowered = followup_text.lower()
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
        "followup_reports_ma_rsi_macd": all(
            token in lowered for token in ("ma", "rsi", "macd")
        ),
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
    key, base_url, model = Config.resolve(backend)
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
    """Multi-provider policy: any eligible backend may close the experiment."""
    per_backend = {}
    for run in runs:
        backend = run.get("backend")
        if not run.get("started"):
            per_backend[backend] = {"started": False, "error": run.get("error")}
            continue
        per_backend[backend] = {
            "started": True,
            "requested_model": run.get("requested_model"),
            "asean_passed": run.get("asean_validation", {}).get("passed") is True,
            "clarification_passed": run.get("clarification", {})
            .get("validation", {})
            .get("passed")
            is True,
        }
    accepting = next(
        (
            backend
            for backend in ACCEPTANCE_BACKENDS
            if per_backend.get(backend, {}).get("asean_passed")
            and per_backend.get(backend, {}).get("clarification_passed")
        ),
        None,
    )
    eligible_attempted = [
        backend for backend in ACCEPTANCE_BACKENDS if backend in per_backend
    ]
    return {
        "policy": (
            "multi-provider: acceptance is not gated on the official OpenAI "
            "account; any provider whose Responses API closes the hosted "
            "search + code-execution loop server-side is eligible"
        ),
        "eligible_acceptance_backends": list(ACCEPTANCE_BACKENDS),
        "eligible_backends_attempted": eligible_attempted,
        "acceptance_backend": accepting,
        "per_backend": per_backend,
        "openrouter_is_diagnostic_not_acceptance": "openrouter" in per_backend,
        "passed": accepting is not None,
        "reference_docs": [
            "https://developers.openai.com/api/docs/guides/tools-web-search",
            "https://developers.openai.com/api/docs/guides/tools-code-interpreter",
            "https://help.aliyun.com/zh/model-studio/qwen-code-interpreter",
        ],
    }


def write_json(path: Path, value: Dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    path.write_text(payload, encoding="utf-8")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def assert_credential_free(payloads: Iterable[str]) -> None:
    """Refuse to write evidence that embeds any configured API key."""
    secrets = [
        value
        for value in (
            Config.OPENAI_API_KEY,
            Config.OPENROUTER_API_KEY,
            Config.DASHSCOPE_API_KEY,
            os.getenv("MOONSHOT_API_KEY", ""),
            os.getenv("KIMI_API_KEY", ""),
            os.getenv("ARK_API_KEY", ""),
            os.getenv("SILICONFLOW_API_KEY", ""),
            os.getenv("GEMINI_API_KEY", ""),
        )
        if value
    ]
    for payload in payloads:
        for secret in secrets:
            if secret in payload:
                raise SystemExit(
                    "Refusing to write evidence: an API key value appears in the payload"
                )
        if "authorization" in payload.lower() and "bearer" in payload.lower():
            raise SystemExit(
                "Refusing to write evidence: an Authorization header appears in the payload"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backends",
        nargs="+",
        choices=["openai", "openrouter", "dashscope"],
        default=["openai", "dashscope"],
    )
    parser.add_argument(
        "--reasoning", choices=["low", "medium", "high", "xhigh", "max"], default="high"
    )
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    runs = [run_backend(backend, args.reasoning) for backend in args.backends]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path("validation") / "runs" / f"real_{stamp}"
    evidence = {
        "schema_version": "1.1",
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
        "independent_asean_reference": independent_asean_reference(),
        "runs": runs,
    }
    evidence["acceptance"] = acceptance(runs)

    receipts = {
        "schema_version": "1.0",
        "experiment_id": "1-3",
        "created_at": evidence["created_at"],
        "note": "Raw credential-free provider turns; no API keys or Authorization headers.",
        "turns": [
            {"backend": run.get("backend"), "api_turns": run.get("api_turns") or []}
            for run in runs
        ],
    }

    evidence_json = json.dumps(evidence, ensure_ascii=False, indent=2)
    receipts_json = json.dumps(receipts, ensure_ascii=False, indent=2)
    assert_credential_free((evidence_json, receipts_json))

    evidence_path = output_dir / "evidence.json"
    evidence_digest = write_json(evidence_path, evidence)
    receipts_digest = write_json(output_dir / "receipts.json", receipts)
    (output_dir / "evidence.sha256").write_text(
        f"{evidence_digest}  evidence.json\n", encoding="utf-8"
    )
    (output_dir / "receipts.sha256").write_text(
        f"{receipts_digest}  receipts.json\n", encoding="utf-8"
    )
    manifest = {
        "schema_version": "1.0",
        "experiment_id": "1-3",
        "run_id": output_dir.name,
        "created_at": evidence["created_at"],
        "artifacts": {
            "evidence.json": {"sha256": evidence_digest},
            "receipts.json": {"sha256": receipts_digest},
        },
        "inputs": {
            "canonical_source": evidence["canonical_source"],
            "backends": args.backends,
            "reasoning": args.reasoning,
        },
        "repository": evidence["repository"],
        "acceptance_passed": evidence["acceptance"]["passed"],
        "acceptance_backend": evidence["acceptance"]["acceptance_backend"],
    }
    manifest_digest = write_json(output_dir / "manifest.json", manifest)

    Path("validation").mkdir(exist_ok=True)
    shutil.copyfile(evidence_path, Path("validation/latest.json"))
    latest = json.loads(Path("validation/latest.json").read_text(encoding="utf-8"))
    latest["artifact_hashes"] = {
        "evidence.json": evidence_digest,
        "receipts.json": receipts_digest,
        "manifest.json": manifest_digest,
        "run_dir": str(output_dir),
    }
    Path("validation/latest.json").write_text(
        json.dumps(latest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(evidence["acceptance"], ensure_ascii=False, indent=2))
    print(f"Evidence: {evidence_path}")
    return 0 if evidence["acceptance"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
