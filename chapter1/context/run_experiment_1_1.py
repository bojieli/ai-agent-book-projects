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

from agent import HIDDEN_RESULT_STYLES, ContextAwareAgent, ContextMode
from config import PROVIDERS, SUPPORTED_PROVIDERS, canonical_provider
from grounding import assess_groundedness, observation_quantities


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

# The sentence above that forbids self-estimated rates is a guard, and whether
# it is present changes what the no-tool-definitions arm does: with it, a model
# that cannot convert says so; without it, some models state rates from memory
# instead.  Both are worth running, so the guard is a flag rather than an
# assumption baked into the task.  Only the guarded task is canonical, because
# it is the one the manuscript describes.
ESTIMATION_GUARD = """Do not estimate exchange
rates yourself; use the tool observations."""
UNGUARDED_TASK = CANONICAL_TASK.replace(ESTIMATION_GUARD, "").rstrip()
TASK_VARIANTS = {"guarded": CANONICAL_TASK, "unguarded": UNGUARDED_TASK}


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


def provider_spec(provider: str):
    """Look the provider up in the shared registry.

    Args:
        provider: A provider name or alias accepted by
            :mod:`agentbook.providers`.

    Returns:
        The registered provider specification.

    Raises:
        RuntimeError: If the name resolves to no registry entry.
    """
    try:
        return PROVIDERS[canonical_provider(provider)]
    except KeyError:
        raise RuntimeError(f"Unknown provider: {provider!r}") from None


def resolve_key(provider: str) -> tuple[str, str]:
    """Find this provider's own credential, refusing to fall back.

    The registry's :func:`resolve_backend` would happily reroute through
    OpenRouter when a provider's key is missing.  That is right for a reader
    running the demo and wrong here: the evidence file claims direct-API
    provenance, so a missing key must stop the run rather than quietly change
    which endpoint answered.

    Args:
        provider: A provider name or alias.

    Returns:
        The key and the environment variable it came from.

    Raises:
        RuntimeError: If none of the provider's key variables are set.
    """
    spec = provider_spec(provider)
    for name in spec.key_vars:
        value = os.getenv(name)
        if value:
            return value, name
    raise RuntimeError(
        f"No direct credential for {provider}; expected one of "
        f"{', '.join(spec.key_vars) or '(none)'}"
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


def evaluate_context_contract(
    mode: str,
    turns: List[Dict[str, Any]],
    hidden_result_content: str = HIDDEN_RESULT_STYLES["empty"],
) -> Dict[str, Any]:
    """Verify the actual provider request, not the requested CLI mode.

    Args:
        mode: The ablation arm being checked.
        turns: The arm's recorded API turns.
        hidden_result_content: What the no-tool-results arm was configured to
            put in place of an observation. Checked exactly, so a real result
            leaking through still fails the contract.

    Returns:
        The per-check details plus a ``passed`` verdict.

    Raises:
        ValueError: If ``mode`` names no known arm.
    """
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
                    m.get("content") == hidden_result_content for m in tool_messages
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


def arm_outcome(completed: bool, correct: bool, verdict: str) -> str:
    """Collapse an arm into the one word the ablation table should show.

    ``Completed`` cannot distinguish the two ways an ablated arm ends without
    the right answer, and they are not equally bad: a model that claims no
    figure it was never given has failed safely, while one that supplies the
    exchange rates from memory has produced a wrong number that reads exactly
    like a right one.

    The labels describe what was measured and nothing more.
    ``no_unsupported_numbers`` covers a principled refusal and a turn that
    merely announced what it was about to do and stopped -- telling those two
    apart is a judgment about intent that this harness has no way to make.

    Args:
        completed: Whether the model returned a terminal response at all.
        correct: Whether that response satisfies the task's answer rubric.
        verdict: The groundedness verdict from
            :func:`grounding.assess_groundedness`.

    Returns:
        One of ``no_terminal_response``, ``correct``, ``unsupported_numbers``,
        ``no_unsupported_numbers`` or ``incorrect``.
    """
    if not completed:
        return "no_terminal_response"
    if correct:
        return "correct"
    if verdict == "ungrounded":
        return "unsupported_numbers"
    if verdict in ("grounded", "no_quantities"):
        return "no_unsupported_numbers"
    return "incorrect"


def sent_messages(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten every message that actually went out on the wire.

    Args:
        turns: The arm's recorded API turns.

    Returns:
        The concatenated request message lists, in turn order.
    """
    return [
        message
        for turn in turns
        for message in (turn.get("request") or {}).get("messages", [])
    ]


def summarize_arm(
    mode: ContextMode,
    result: Dict[str, Any],
    elapsed: float,
    task_text: str = CANONICAL_TASK,
    hidden_result_content: str = HIDDEN_RESULT_STYLES["empty"],
) -> Dict[str, Any]:
    trajectory = result["trajectory"]
    tool_calls = [tool_call_dict(call) for call in trajectory.tool_calls]
    signatures = call_signatures(tool_calls)
    repeats = len(signatures) - len(set(signatures))
    final_answer = result.get("final_answer")
    completed = bool(result.get("completed", result.get("success", False)))
    task_success = canonical_answer_correct(final_answer)
    # Groundedness is read from the messages the model received, not from the
    # tool results the harness computed.  In the no-tool-results arm those two
    # differ by design, and only the former is what the model had to reason
    # from.
    observations = observation_quantities(sent_messages(trajectory.api_turns))
    groundedness = assess_groundedness(final_answer, task_text, observations)
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
    arm["context_contract"] = evaluate_context_contract(
        mode.value, trajectory.api_turns, hidden_result_content
    )
    arm["groundedness"] = groundedness
    arm["outcome"] = arm_outcome(completed, task_success, groundedness["verdict"])
    arm["behavior"] = {
        "tool_action_count": len(tool_calls),
        "has_repeated_tool_action": repeats > 0,
        "hit_iteration_ceiling": result.get("iterations") >= 5 and not completed,
        "canonical_answer_correct": task_success,
        "stated_unsupported_numbers": groundedness["verdict"] == "ungrounded",
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


def arm_produced_inference(arm: Dict[str, Any] | None) -> bool:
    """Report whether this arm actually got answers from the provider.

    Two of the manuscript's four behaviour claims are phrased as absences --
    no tool action, no correct answer -- and an arm that never reached the
    provider satisfies both.  Without this check a run whose every request
    returned 402 would report three of the four claims as "observed", which is
    the one thing an evidence file must never do.

    Args:
        arm: A summarised arm, or ``None`` when the mode was not run.

    Returns:
        ``True`` if every recorded turn carries a provider response id and the
        arm recorded no transport error.
    """
    if not arm or arm.get("error") or not arm.get("api_turns"):
        return False
    return all(turn.get("response", {}).get("id") for turn in arm["api_turns"])


CLAIM_QUALIFICATIONS = {
    "without_tool_definitions_no_tool_action": (
        "Vacuous by construction: the request carries no tool definitions, so "
        "the provider cannot emit a tool call. What varies between models is "
        "what they do instead -- see arm_outcomes.no_tool_calls, which "
        "separates claiming no figure the model was not given from an "
        "answer built on exchange rates it supplied itself."
    ),
    "without_reasoning_degraded": (
        "Inferred from loss of canonical correctness, and note what this arm "
        "removes: retained reasoning is stripped from the history, while the "
        "model still reasons afresh on every turn. It therefore tests whether "
        "carrying prior reasoning forward matters, which it need not when each "
        "step is already determined by the previous observation. A stronger "
        "claim -- that the ablation produces contradictory decisions -- is not "
        "something the harness can force, and has not been observed."
    ),
}


def claim(value: bool, evaluable: bool) -> bool | None:
    """Return an observation, or ``None`` when there was nothing to observe.

    Args:
        value: The claim's value as computed from the arm.
        evaluable: Whether the arm produced a real inference.

    Returns:
        ``value`` when the arm is evaluable, otherwise ``None``.
    """
    return value if evaluable else None


def analyze(arms: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_mode = {arm["mode"]: arm for arm in arms}
    exact_five_arms = set(by_mode) == {mode.value for mode in MODES}
    contracts_pass = exact_five_arms and all(
        arm["context_contract"]["passed"] for arm in arms
    )
    direct_real_api = bool(arms) and all(
        not arm["using_openrouter"] and arm_produced_inference(arm) for arm in arms
    )
    live = {mode: arm_produced_inference(by_mode.get(mode)) for mode in by_mode}

    def behavior_of(mode: str, key: str, default: Any = False) -> Any:
        return by_mode.get(mode, {}).get("behavior", {}).get(key, default)

    behavior = {
        "full_baseline_correct": claim(
            bool(behavior_of("full", "canonical_answer_correct")), live.get("full", False)
        ),
        "without_tool_definitions_no_tool_action": claim(
            behavior_of("no_tool_calls", "tool_action_count", None) == 0,
            live.get("no_tool_calls", False),
        ),
        "without_tool_results_repeated_action": claim(
            bool(behavior_of("no_tool_results", "has_repeated_tool_action")),
            live.get("no_tool_results", False),
        ),
        "without_history_repeated_action": claim(
            bool(behavior_of("no_history", "has_repeated_tool_action")),
            live.get("no_history", False),
        ),
        # Contradiction is an empirical outcome, not something the harness can
        # legitimately force.  We report whether the no-reasoning answer lost
        # canonical correctness and keep this separate from execution validity.
        "without_reasoning_degraded": claim(
            not behavior_of("no_reasoning", "canonical_answer_correct"),
            live.get("no_reasoning", False),
        ),
    }
    behavior["all_manuscript_behavior_claims_observed"] = all(
        value is True for value in behavior.values()
    )
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
        "claim_qualifications": CLAIM_QUALIFICATIONS,
        # What each arm actually did, which is the part ``Completed`` hides:
        # an abstention and an answer assembled from remembered exchange rates
        # are both terminal responses.
        "arm_outcomes": {arm["mode"]: arm["outcome"] for arm in arms},
        "arms_stating_unsupported_numbers": [
            arm["mode"] for arm in arms if arm["groundedness"]["verdict"] == "ungrounded"
        ],
        "usage": token_usage(arms),
    }


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        default="kimi",
        choices=SUPPORTED_PROVIDERS,
        help="Provider to run every arm against (default: kimi).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model id. Defaults to the chosen provider's registry default, so "
             "--provider alone is enough; naming a model from another provider "
             "is what makes every arm fail with a 400.",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=[mode.value for mode in MODES],
        help="Arms to run (default: all five). A subset is a probe, not a "
             "canonical run, and is never promoted to validation/latest.json.",
    )
    parser.add_argument(
        "--task",
        default="guarded",
        choices=sorted(TASK_VARIANTS),
        help="guarded (default, canonical) forbids self-estimated exchange "
             "rates; unguarded drops that sentence to see what a model does "
             "when nothing tells it not to guess.",
    )
    parser.add_argument(
        "--hidden-result",
        default="empty",
        choices=sorted(HIDDEN_RESULT_STYLES),
        help="How the no-tool-results arm withholds an observation. empty "
             "(default, canonical) withholds silently, which is what removing "
             "the tool results means; marker leaves a visible redaction, which "
             "adds a signal the ablation was supposed to take away and lets "
             "the model notice and stop.",
    )
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.max_iterations < 2:
        parser.error("--max-iterations must be at least 2")

    # An unset --model means "whatever this provider's default is", resolved
    # from the shared registry rather than from a constant that happens to name
    # one provider's model.
    model = args.model or provider_spec(args.provider).default_model
    modes = [ContextMode(name) for name in args.modes] if args.modes else list(MODES)
    task = TASK_VARIANTS[args.task]
    hidden_result_content = HIDDEN_RESULT_STYLES[args.hidden_result]
    canonical_run = (
        args.task == "guarded"
        and args.hidden_result == "empty"
        and set(modes) == set(MODES)
    )

    key, key_env = resolve_key(args.provider)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or Path("validation") / f"real_{stamp}"
    command = [
        sys.executable,
        Path(__file__).name,
        "--provider",
        args.provider,
        "--model",
        model,
        "--task",
        args.task,
        "--hidden-result",
        args.hidden_result,
        "--modes",
        *[mode.value for mode in modes],
        "--max-iterations",
        str(args.max_iterations),
        "--output-dir",
        str(output_dir),
    ]

    arms = []
    for mode in modes:
        started = utc_now()
        agent = ContextAwareAgent(
            key,
            context_mode=mode,
            provider=args.provider,
            model=model,
            verbose=False,
            hidden_result_content=hidden_result_content,
        )
        begin = time.monotonic()
        result = agent.execute_task(task, max_iterations=args.max_iterations)
        arm = summarize_arm(
            mode,
            result,
            time.monotonic() - begin,
            task_text=task,
            hidden_result_content=hidden_result_content,
        )
        arm["started_at"] = started
        # Recompute the configured ceiling rather than retaining the default in
        # the pure summarizer (which is also exercised by unit tests).
        arm["behavior"]["hit_iteration_ceiling"] = (
            result.get("iterations") >= args.max_iterations and not result.get("success")
        )
        arms.append(arm)

    evidence: Dict[str, Any] = {
        "schema_version": "1.1",
        "experiment_id": EXPERIMENT_ID,
        "evidence_mode": "real_api",
        "created_at": utc_now(),
        "canonical_source": "book/chapter1.md#实验-1-1-上下文的关键作用",
        "task": task,
        "task_variant": args.task,
        "hidden_result_style": args.hidden_result,
        "canonical_run": canonical_run,
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
    # validation/latest.json is what the ledger cites, so only a run that is
    # both canonical and accepted may replace it.  A probe -- a subset of arms,
    # the unguarded task, or a run whose requests never landed -- keeps its own
    # timestamped directory and leaves the cited evidence alone.
    promoted = canonical_run and evidence["analysis"]["experiment_execution_accepted"]
    if promoted:
        latest = Path("validation/latest.json")
        latest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(evidence_path, latest)

    print(json.dumps(evidence["analysis"], ensure_ascii=False, indent=2))
    print(f"Evidence: {evidence_path}")
    print(f"SHA-256: {digest}")
    print(
        "Promoted to validation/latest.json"
        if promoted
        else "Not promoted to validation/latest.json "
             f"(canonical_run={canonical_run}, "
             f"accepted={evidence['analysis']['experiment_execution_accepted']})"
    )
    return 0 if evidence["analysis"]["experiment_execution_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
