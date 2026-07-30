#!/usr/bin/env python3
"""Run Experiment 1-2 through Kimi K3's official Formula web-search tool."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from agent import WebSearchAgent, is_failure_answer


QUESTION = """截至 2026 年 7 月 30 日，请核查东盟成员资格和印度尼西亚首都的最新状态。
请自主完成研究：先搜索东盟成员国的官方来源，确认当前成员数量、成员名单及东帝汶正式入盟日期；
检查第一轮证据还缺什么，然后至少再执行一次不同的后续搜索，核实雅加达与努山塔拉的当前法律地位以及总统令是否已生效。
最后给出结构化结论、检索日期和可点击的权威来源链接。不要依赖记忆作答。"""


def git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


FORMULA_URI = "moonshot/web-search:latest"


def response_ids(turns: List[Dict[str, Any]]) -> List[str]:
    return [
        turn.get("response", {}).get("id")
        for turn in turns
        if turn.get("kind") == "chat_completion"
        if turn.get("response", {}).get("id")
    ]


def fiber_ids(turns: List[Dict[str, Any]]) -> List[str]:
    """Return only real, succeeded Formula Fiber receipts."""
    return [
        turn.get("response", {}).get("id")
        for turn in turns
        if turn.get("kind") == "formula_fiber"
        and turn.get("http_status") == 200
        and turn.get("response", {}).get("status") == "succeeded"
        and turn.get("response", {}).get("id")
    ]


def has_web_search_declaration(tools: List[Dict[str, Any]]) -> bool:
    return any(
        tool.get("type") == "function"
        and tool.get("function", {}).get("name") == "web_search"
        and isinstance(tool.get("function", {}).get("parameters"), dict)
        for tool in tools
    )


def usage(turns: List[Dict[str, Any]]) -> Dict[str, int]:
    prompt = completion = cached = reasoning = 0
    for turn in turns:
        if turn.get("kind") != "chat_completion":
            continue
        item = turn.get("response", {}).get("usage") or {}
        prompt += int(item.get("prompt_tokens") or 0)
        completion += int(item.get("completion_tokens") or 0)
        cached += int((item.get("prompt_tokens_details") or {}).get("cached_tokens") or 0)
        reasoning += int(
            (item.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
        )
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "cached_prompt_tokens": cached,
        "reasoning_tokens": reasoning,
    }


def validate(payload: Dict[str, Any]) -> Dict[str, Any]:
    trace = payload["trace"]
    turns = payload["api_turns"]
    chat_turns = [t for t in turns if t.get("kind") == "chat_completion"]
    declaration_turns = [t for t in turns if t.get("kind") == "formula_tools"]
    fiber_turns = [t for t in turns if t.get("kind") == "formula_fiber"]
    ids = fiber_ids(turns)
    search_actions = [
        step
        for step in trace
        if step.get("type") == "action" and step.get("tool") == "web_search"
    ]
    answer = payload["answer"]
    answer_lower = answer.lower()
    checks = {
        "direct_moonshot_api": payload["provider"] == "moonshot"
        and payload["base_url"].rstrip("/") == "https://api.moonshot.cn/v1",
        "exact_model": payload["model"] == "kimi-k3",
        "one_real_formula_declaration_fetch": len(declaration_turns) == 1
        and declaration_turns[0].get("formula_uri") == FORMULA_URI
        and declaration_turns[0].get("http_status") == 200
        and not declaration_turns[0].get("error"),
        "provider_formula_declares_standard_web_search": len(declaration_turns) == 1
        and has_web_search_declaration(
            declaration_turns[0].get("response", {}).get("tools", [])
        ),
        "provider_response_each_chat_turn": len(response_ids(turns)) == len(chat_turns)
        and len(chat_turns) >= 3,
        "formula_tool_declared_each_chat_turn": bool(chat_turns)
        and all(
            has_web_search_declaration(turn.get("request", {}).get("tools", []))
            for turn in chat_turns
        ),
        "all_fibers_succeeded": len(fiber_turns) >= 2
        and len(ids) == len(fiber_turns),
        "multiple_distinct_formula_fibers": len(ids) >= 2
        and len(set(ids)) >= 2,
        "fiber_requests_match_model_actions": len(fiber_turns) == len(search_actions)
        and all(
            turn.get("formula_uri") == FORMULA_URI
            and turn.get("request", {}).get("body", {}).get("name") == "web_search"
            and isinstance(
                turn.get("request", {}).get("body", {}).get("arguments"), str
            )
            for turn in fiber_turns
        ),
        "sequential_search_rounds_observed": len(
            {step.get("iteration") for step in search_actions}
        )
        >= 2,
        "reasoning_observed": any(step.get("type") == "thought" for step in trace),
        "final_answer_observed": any(step.get("type") == "answer" for step in trace)
        and not is_failure_answer(answer),
        "source_links_in_answer": "http://" in answer or "https://" in answer,
        "official_sources_in_answer": "asean.org" in answer_lower
        and any(
            domain in answer_lower
            for domain in ("go.id", "polri.go.id", "mkri.id")
        ),
        "current_eleven_member_fact": any(
            marker in answer_lower for marker in ("11", "十一")
        )
        and any(
            marker in answer_lower for marker in ("timor-leste", "东帝汶")
        ),
        "timor_leste_admission_date": "2025" in answer_lower
        and any(marker in answer_lower for marker in ("10月26", "10 月 26", "10-26", "october 26")),
        "indonesia_capital_transition_explained": any(
            marker in answer_lower for marker in ("jakarta", "雅加达")
        )
        and any(
            marker in answer_lower for marker in ("nusantara", "努山塔拉")
        )
        and any(
            marker in answer_lower
            for marker in ("presidential decree", "presidential decision", "总统令")
        ),
        "retrieval_date_reported": "2026" in answer_lower
        and any(marker in answer_lower for marker in ("7月30", "7 月 30", "2026-07-30")),
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "formula_uri": FORMULA_URI,
        "fiber_ids": ids,
        "usage": usage(turns),
    }


def write_json(path: Path, value: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_once(model: str, timeout: float) -> Dict[str, Any]:
    key = os.getenv("MOONSHOT_API_KEY") or os.getenv("KIMI_API_KEY")
    if not key:
        raise RuntimeError("MOONSHOT_API_KEY or KIMI_API_KEY is required")
    # The SDK retries transport failures; experiment-level retries below are
    # reserved for Moonshot's explicit transient engine-overload response.
    os.environ["SEARCH_TIMEOUT"] = str(timeout)
    agent = WebSearchAgent(api_key=key, model=model, verbose=True)
    answer = agent.search_and_answer(QUESTION, max_iterations=8)
    return {
        "provider": "openrouter" if agent.using_openrouter else "moonshot",
        "model": agent.model,
        "base_url": agent.base_url,
        "question": QUESTION,
        "answer": answer,
        "trace": agent.get_trace(),
        "api_turns": agent.get_api_turns(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="kimi-k3")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.model != "kimi-k3":
        parser.error("Experiment 1-2 requires the exact kimi-k3 model")

    failures = []
    run = None
    for attempt in range(1, args.attempts + 1):
        candidate = run_once(args.model, args.timeout)
        validation = validate(candidate)
        if validation["passed"]:
            run = candidate
            break
        failures.append(
            {
                "attempt": attempt,
                "answer": candidate["answer"],
                "validation": validation,
                "api_turns": candidate["api_turns"],
            }
        )
        if attempt == args.attempts:
            run = candidate
            break
        # Kimi K3 can occasionally stop after a tool round, and Formula Fibers
        # can transiently overload.  Both
        # are honest failed attempts; retry the whole independent run and keep
        # every failed API trace in the final evidence.
        time.sleep(2**attempt)
    assert run is not None

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path("validation") / f"real_{stamp}"
    evidence = {
        "schema_version": "2.0",
        "experiment_id": "1-2",
        "evidence_mode": "real_api",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_source": "book/chapter1.md#实验-1-2-kimi-k3-原生-agent-能力",
        "credential_source_env": "MOONSHOT_API_KEY"
        if os.getenv("MOONSHOT_API_KEY")
        else "KIMI_API_KEY",
        "credential_value_recorded": False,
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
        "transient_failed_attempts": failures,
        "run": run,
    }
    evidence["acceptance"] = validate(run)
    evidence_path = output_dir / "evidence.json"
    write_json(evidence_path, evidence)
    digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    (output_dir / "evidence.sha256").write_text(
        f"{digest}  evidence.json\n", encoding="utf-8"
    )
    Path("validation").mkdir(exist_ok=True)
    shutil.copyfile(evidence_path, Path("validation/latest.json"))
    print(json.dumps(evidence["acceptance"], ensure_ascii=False, indent=2))
    print(f"Evidence: {evidence_path}")
    return 0 if evidence["acceptance"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
