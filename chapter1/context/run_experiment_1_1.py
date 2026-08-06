#!/usr/bin/env python3
"""Run the exact five-arm context ablation from book/chapter1.md.

Unlike the legacy demo table, this runner persists every credential-free API
request and response.  That makes it possible to prove which context component
was removed on every inference instead of inferring the ablation from a CLI
flag after the fact.
"""

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
from typing import Any, Dict, Iterable, List

from agent import ContextAwareAgent, ContextMode


EXPERIMENT_ID = "1-1"
MODES = list(ContextMode)
CANONICAL_TASK = """According to the company's quarterly revenue:
- Q1: 2.5 million USD
- Q2: 2.1 million EUR
- Q3: 1.8 million GBP
- Q4: 380 million JPY

Use the available currency-conversion and calculation tools to convert every
non-USD quarter to USD, then calculate the annual total and quarterly average.
Report both values rounded to two decimal places. Do not estimate exchange
rates yourself; use the tool observations."""

EXPECTED_NUMBERS = ("9602895.73", "2400723.93")
KEY_ENV = {
    "kimi": ("MOONSHOT_API_KEY", "KIMI_API_KEY"),
    "moonshot": ("MOONSHOT_API_KEY", "KIMI_API_KEY"),
    "doubao": ("ARK_API_KEY",),
    "siliconflow": ("SILICONFLOW_API_KEY",),
    "deepseek": ("DEEPSEEK_API_KEY",),
    "openrouter": ("OPENROUTER_API_KEY",),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", *args], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def package_version(distribution: str) -> str | None:
    try:
        from importlib.metadata import version

        return version(distribution)
    except Exception:
        return None


def resolve_key(provider: str) -> tuple[str, str]:
    names = KEY_ENV.get(provider, ())
    for name in names:
        value = os.getenv(name)
        if value:
            return value, name
    raise RuntimeError(
        f"No direct credential for {provider}; expected one of {', '.join(names)}"
    )


def tool_call_dict(call: Any) -> Dict[str, Any]:
    return {
        "tool_name": call.tool_name,
        "arguments": call.arguments,
        "result": call.result,
        "timestamp": call.timestamp,
    }


def call_signatures(tool_calls: Iterable[Dict[str, Any]]) -> List[str]:
    signatures = []
    for call in tool_calls:
        signatures.append(
            f"{call['tool_name']}:"
            + json.dumps(call.get("arguments", {}), sort_keys=True, ensure_ascii=False)
        )
    return signatures


def response_message(turn: Dict[str, Any]) -> Dict[str, Any]:
    choices = turn.get("response", {}).get("choices") or []
    return (choices[0].get("message") or {}) if choices else {}


def request_roles(turn: Dict[str, Any]) -> List[str]:
    return [message.get("role") for message in turn.get("request", {}).get("messages", [])]


def evaluate_context_contract(mode: str, turns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify the actual provider request, not the requested CLI mode."""
    requests = [turn.get("request", {}) for turn in turns if turn.get("request")]
    real_responses = [turn for turn in turns if turn.get("response", {}).get("id")]
    details: Dict[str, Any] = {
        "has_provider_response_ids": len(real_responses) == len(turns) and bool(turns),
        "turn_count": len(turns),
        "request_roles": [request_roles(turn) for turn in turns],
    }

    if mode == ContextMode.FULL.value:
        details.update(
            {
                "tools_present_every_turn": all(bool(r.get("tools")) for r in requests),
                "history_present_after_first_turn": len(requests) > 1
                and all(
                    "assistant" in [m.get("role") for m in r.get("messages", [])]
                    and "tool" in [m.get("role") for m in r.get("messages", [])]
                    for r in requests[1:]
                ),
                "reasoning_retained_after_first_turn": len(requests) > 1
                and any(
                    bool(m.get("reasoning_content"))
                    for m in requests[1].get("messages", [])
                    if m.get("role") == "assistant"
                ),
            }
        )
        required = (
            "has_provider_response_ids",
            "tools_present_every_turn",
            "history_present_after_first_turn",
            "reasoning_retained_after_first_turn",
        )
    elif mode == ContextMode.NO_TOOL_CALLS.value:
        details.update(
            {
                "tools_absent_every_turn": all(
                    "tools" not in r and "tool_choice" not in r for r in requests
                ),
            }
        )
        required = ("has_provider_response_ids", "tools_absent_every_turn")
    elif mode == ContextMode.NO_TOOL_RESULTS.value:
        tool_messages = [
            m
            for r in requests[1:]
            for m in r.get("messages", [])
            if m.get("role") == "tool"
        ]
        details.update(
            {
                "tool_calls_retained": any(
                    m.get("role") == "assistant" and m.get("tool_calls")
                    for r in requests[1:]
                    for m in r.get("messages", [])
                ),
                "tool_results_hidden": bool(tool_messages)
                and all(
                    m.get("content") == "[Tool result hidden due to context mode]"
                    for m in tool_messages
                ),
            }
        )
        required = (
            "has_provider_response_ids",
            "tool_calls_retained",
            "tool_results_hidden",
        )
    elif mode == ContextMode.NO_REASONING.value:
        assistant_history = [
            m
            for r in requests[1:]
            for m in r.get("messages", [])
            if m.get("role") == "assistant"
        ]
        provider_reasoning = [
            response_message(turn).get("reasoning_content") for turn in turns
        ]
        details.update(
            {
                "provider_generated_reasoning": any(provider_reasoning),
                "reasoning_removed_from_history": bool(assistant_history)
                and all(not m.get("reasoning_content") for m in assistant_history),
                "tool_and_result_history_retained": any(
                    "tool" in request_roles(turn) for turn in turns[1:]
                ),
            }
        )
        required = (
            "has_provider_response_ids",
            "provider_generated_reasoning",
            "reasoning_removed_from_history",
            "tool_and_result_history_retained",
        )
    elif mode == ContextMode.NO_HISTORY.value:
        details.update(
            {
                "only_static_prefix_and_user_every_turn": bool(requests)
                and all(
                    [m.get("role") for m in r.get("messages", [])]
                    == ["system", "user"]
                    for r in requests
                ),
                "tools_still_present": all(bool(r.get("tools")) for r in requests),
            }
        )
        required = (
            "has_provider_response_ids",
            "only_static_prefix_and_user_every_turn",
            "tools_still_present",
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

    details["required_checks"] = list(required)
    details["passed"] = all(details[name] is True for name in required)
    return details


def normalized_number_text(value: str | None) -> str:
    return (value or "").replace(",", "").replace("$", "").replace(" ", "")


def canonical_answer_correct(final_answer: str | None) -> bool:
    """Evaluate the known numeric rubric for the canonical Experiment 1-1 task.

    This is deliberately kept outside ``ContextAwareAgent``.  A generic agent
    cannot infer correctness from an arbitrary natural-language task, while
    this experiment has an explicit answer rubric.
    """
    normalized = normalized_number_text(final_answer)
    return bool(final_answer) and all(number in normalized for number in EXPECTED_NUMBERS)


def summarize_arm(mode: ContextMode, result: Dict[str, Any], elapsed: float) -> Dict[str, Any]:
    trajectory = result["trajectory"]
    tool_calls = [tool_call_dict(call) for call in trajectory.tool_calls]
    signatures = call_signatures(tool_calls)
    repeats = len(signatures) - len(set(signatures))
    final_answer = result.get("final_answer")
    completed = bool(result.get("completed", result.get("success", False)))
    task_success = canonical_answer_correct(final_answer)
    arm = {
        "mode": mode.value,
        "provider": result.get("provider"),
        "model": result.get("model"),
        "base_url": result.get("base_url"),
        "using_openrouter": result.get("using_openrouter", False),
        "started_at": None,
        "elapsed_seconds": round(elapsed, 6),
        # ``success`` is retained for compatibility with existing evidence;
        # it means terminal response/completion, not task correctness.
        "success": completed,
        "completed": completed,
        "task_success": task_success,
        "iterations": result.get("iterations", 0),
        "error": result.get("error"),
        "final_answer": final_answer,
        "tool_calls": tool_calls,
        "tool_call_signatures": signatures,
        "repeated_tool_calls": repeats,
        "reasoning_steps": trajectory.reasoning_steps,
        "api_turns": trajectory.api_turns,
    }
    arm["context_contract"] = evaluate_context_contract(mode.value, trajectory.api_turns)
    arm["behavior"] = {
        "tool_action_count": len(tool_calls),
        "has_repeated_tool_action": repeats > 0,
        "hit_iteration_ceiling": result.get("iterations") >= 5 and not completed,
        "canonical_answer_correct": task_success,
    }
    return arm


def token_usage(arms: List[Dict[str, Any]]) -> Dict[str, int]:
    prompt = completion = cached = reasoning = 0
    for arm in arms:
        for turn in arm["api_turns"]:
            usage = turn.get("response", {}).get("usage") or {}
            prompt += int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
            completion += int(
                usage.get("completion_tokens") or usage.get("output_tokens") or 0
            )
            prompt_details = usage.get("prompt_tokens_details") or usage.get(
                "input_tokens_details"
            ) or {}
            completion_details = usage.get("completion_tokens_details") or usage.get(
                "output_tokens_details"
            ) or {}
            cached += int(prompt_details.get("cached_tokens") or 0)
            reasoning += int(completion_details.get("reasoning_tokens") or 0)
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": prompt + completion,
        "cached_prompt_tokens": cached,
        "reasoning_tokens": reasoning,
    }


def analyze(arms: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_mode = {arm["mode"]: arm for arm in arms}
    exact_five_arms = set(by_mode) == {mode.value for mode in MODES}
    contracts_pass = exact_five_arms and all(
        arm["context_contract"]["passed"] for arm in arms
    )
    direct_real_api = all(
        not arm["using_openrouter"]
        and arm["api_turns"]
        and all(turn.get("response", {}).get("id") for turn in arm["api_turns"])
        for arm in arms
    )
    behavior = {
        "full_baseline_correct": by_mode.get("full", {}).get("behavior", {}).get(
            "canonical_answer_correct", by_mode.get("full", {}).get("task_success", False)
        ),
        "without_tool_definitions_no_tool_action": by_mode.get(
            "no_tool_calls", {}
        ).get("behavior", {}).get("tool_action_count")
        == 0,
        "without_tool_results_repeated_action": by_mode.get(
            "no_tool_results", {}
        ).get("behavior", {}).get("has_repeated_tool_action", False),
        "without_history_repeated_action": by_mode.get("no_history", {}).get(
            "behavior", {}
        ).get("has_repeated_tool_action", False),
        # Contradiction is an empirical outcome, not something the harness can
        # legitimately force.  We report whether the no-reasoning answer lost
        # canonical correctness and keep this separate from execution validity.
        "without_reasoning_degraded": not by_mode.get("no_reasoning", {}).get(
            "behavior", {}
        ).get("canonical_answer_correct", False),
    }
    behavior["all_manuscript_behavior_claims_observed"] = all(behavior.values())
    return {
        "exact_five_arms_present": exact_five_arms,
        "all_context_contracts_passed": contracts_pass,
        "direct_real_api_evidence": direct_real_api,
        "experiment_execution_accepted": bool(
            exact_five_arms
            and contracts_pass
            and direct_real_api
            and behavior["full_baseline_correct"]
        ),
        "manuscript_behavior_claims": behavior,
        "usage": token_usage(arms),
    }


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", default="kimi", choices=sorted(KEY_ENV))
    parser.add_argument("--model", default="kimi-k3")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.max_iterations < 2:
        parser.error("--max-iterations must be at least 2")

    key, key_env = resolve_key(args.provider)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path("validation") / f"real_{stamp}"
    command = [
        sys.executable,
        Path(__file__).name,
        "--provider",
        args.provider,
        "--model",
        args.model,
        "--max-iterations",
        str(args.max_iterations),
        "--output-dir",
        str(output_dir),
    ]

    arms = []
    for mode in MODES:
        started = utc_now()
        agent = ContextAwareAgent(
            key,
            context_mode=mode,
            provider=args.provider,
            model=args.model,
            verbose=False,
        )
        begin = time.monotonic()
        result = agent.execute_task(CANONICAL_TASK, max_iterations=args.max_iterations)
        arm = summarize_arm(mode, result, time.monotonic() - begin)
        arm["started_at"] = started
        # Recompute the configured ceiling rather than retaining the default in
        # the pure summarizer (which is also exercised by unit tests).
        arm["behavior"]["hit_iteration_ceiling"] = (
            result.get("iterations") >= args.max_iterations and not result.get("success")
        )
        arms.append(arm)

    evidence: Dict[str, Any] = {
        "schema_version": "1.0",
        "experiment_id": EXPERIMENT_ID,
        "evidence_mode": "real_api",
        "created_at": utc_now(),
        "canonical_source": "book/chapter1.md#实验-1-1-上下文的关键作用",
        "task": CANONICAL_TASK,
        "expected_numbers": list(EXPECTED_NUMBERS),
        "command": command,
        "credential_source_env": key_env,
        "credential_value_recorded": False,
        "host": {
            "platform": platform.platform(),
            "python": sys.version,
            "machine": platform.machine(),
        },
        "dependencies": {
            "openai": package_version("openai"),
            "requests": package_version("requests"),
        },
        "repository": {
            "commit": git_value("rev-parse", "HEAD"),
            "branch": git_value("branch", "--show-current"),
            "worktree_dirty": bool(git_value("status", "--porcelain")),
        },
        "arms": arms,
    }
    evidence["analysis"] = analyze(arms)
    evidence_path = output_dir / "evidence.json"
    write_json(evidence_path, evidence)
    digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    (output_dir / "evidence.sha256").write_text(
        f"{digest}  evidence.json\n", encoding="utf-8"
    )
    latest = Path("validation/latest.json")
    latest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(evidence_path, latest)

    print(json.dumps(evidence["analysis"], ensure_ascii=False, indent=2))
    print(f"Evidence: {evidence_path}")
    print(f"SHA-256: {digest}")
    return 0 if evidence["analysis"]["experiment_execution_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
