"""Fixed structural and real-run validation for Experiment 5-13."""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "agent.py",
    "domain_tools.py",
    "main.py",
    "system_prompt.md",
    "tools.json",
    "requirements.txt",
    "tests/test_contract.py",
}


@dataclass
class ValidationReport:
    structural_ok: bool
    compile_ok: bool
    tests_ok: bool
    live_ok: bool | None
    protocol_ok: bool | None
    multiturn_ok: bool | None
    raw_evidence_ok: bool | None
    usage_ok: bool | None
    semantic_ok: bool | None
    duration_s: float
    errors: list[str]
    live_result: dict[str, Any] | None = None
    semantic_judgment: dict[str, Any] | None = None
    live_cases: list[dict[str, Any]] = field(default_factory=list)
    quality_score: int = 0
    quality_max_score: int = 0

    @property
    def ok(self) -> bool:
        optional_gates = (
            self.live_ok,
            self.protocol_ok,
            self.multiturn_ok,
            self.raw_evidence_ok,
            self.usage_ok,
            self.semantic_ok,
        )
        return (
            self.structural_ok
            and self.compile_ok
            and self.tests_ok
            and all(value is not False for value in optional_gates)
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ok"] = self.ok
        return payload


def _attribute_name(node: ast.AST) -> str:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _structural_check(root: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    missing = sorted(path for path in REQUIRED_FILES if not (root / path).is_file())
    if missing:
        errors.append(f"missing required files: {', '.join(missing)}")
    trees: dict[str, ast.AST] = {}
    sources: dict[str, str] = {}
    for relative in ("agent.py", "domain_tools.py", "main.py"):
        path = root / relative
        if path.exists():
            sources[relative] = path.read_text(encoding="utf-8")
            try:
                trees[relative] = ast.parse(sources[relative], filename=str(path))
            except SyntaxError as exc:
                errors.append(f"{relative}: {exc}")
    tools_path = root / "tools.json"
    if tools_path.exists():
        try:
            tools = json.loads(tools_path.read_text(encoding="utf-8"))["tools"]
            names = [tool["function"]["name"] for tool in tools]
            if not names or len(names) != len(set(names)):
                errors.append("tools.json must contain unique function names")
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid tools.json: {exc}")

    agent_tree = trees.get("agent.py")
    if agent_tree is not None:
        string_constants = {
            node.value
            for node in ast.walk(agent_tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        attributes = {
            _attribute_name(node)
            for node in ast.walk(agent_tree)
            if isinstance(node, ast.Attribute)
        }
        for marker in ("assistant", "tool", "tool_call_id", "tool_calls"):
            if marker not in string_constants and not any(
                name.endswith(f".{marker}") for name in attributes
            ):
                errors.append(f"agent loop missing required protocol element: {marker}")
        run_functions = [
            node
            for node in ast.walk(agent_tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "run"
        ]
        run_args = {
            arg.arg
            for function in run_functions
            for arg in (*function.args.args, *function.args.kwonlyargs)
        }
        if "history" not in run_args:
            errors.append("Agent run contract must accept prior multi-turn history")
        has_bound = any(
            isinstance(node, ast.arg) and node.arg in {"max_iterations", "max_steps", "max_turns"}
            for node in ast.walk(agent_tree)
        )
        has_bounded_loop = any(
            isinstance(node, ast.For)
            and isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
            for node in ast.walk(agent_tree)
        )
        if not (has_bound and has_bounded_loop):
            errors.append(
                "agent loop must expose a maximum-iteration bound and use a bounded for/range loop"
            )
        if not any(
            isinstance(node, ast.ImportFrom)
            and node.module == "openai"
            and any(alias.name == "OpenAI" for alias in node.names)
            for node in ast.walk(agent_tree)
        ):
            errors.append("agent.py must use the current OpenAI client class")
        if not any(name.endswith("chat.completions.create") for name in attributes):
            errors.append("agent.py must use the current chat.completions API")
        for evidence_key in ("messages", "usage"):
            if evidence_key not in string_constants:
                errors.append(f"live result must preserve raw {evidence_key} evidence")

    main_tree = trees.get("main.py")
    if main_tree is not None:
        main_strings = {
            node.value
            for node in ast.walk(main_tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        for option in ("--task", "--model", "--history-json"):
            if option not in main_strings:
                errors.append(f"main.py must implement the common live CLI option {option}")

    for file in root.rglob("*"):
        if file.is_file() and file.name != ".env.example":
            text = file.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"\bsk-[A-Za-z0-9_-]{12,}\b", text):
                errors.append(f"possible embedded secret in {file.relative_to(root)}")
    return not errors, errors


def _run(
    command: list[str],
    root: Path,
    timeout: int,
    extra_env: dict[str, str] | None = None,
) -> tuple[bool, str, float]:
    started = time.perf_counter()
    # Generated Agents live below ``runs/`` while the experiment's repository-
    # level pytest.ini is intentionally discovered from a parent directory.
    # Pytest therefore does not reliably prepend the generated Agent root to
    # sys.path.  Make the executable-under-test importable exactly as it is when
    # launched via ``python main.py``; otherwise valid ``import agent`` and
    # ``import domain_tools`` statements fail during collection before a single
    # generated test can run.
    inherited_pythonpath = os.environ.get("PYTHONPATH", "")
    pythonpath = str(root)
    if inherited_pythonpath:
        pythonpath += os.pathsep + inherited_pythonpath
    proc = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        env={
            **os.environ,
            **(extra_env or {}),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": pythonpath,
        },
    )
    return proc.returncode == 0, proc.stdout[-100000:], round(time.perf_counter() - started, 3)


def _contains_all(text: str, expected: list[str]) -> bool:
    folded = text.casefold()
    return all(value.casefold() in folded for value in expected)


def _history_is_preserved(messages: list[Any], history: list[dict[str, Any]]) -> bool:
    if not history:
        return True
    cursor = 0
    for message in messages:
        if cursor >= len(history) or not isinstance(message, dict):
            continue
        expected = history[cursor]
        if message.get("role") == expected["role"] and message.get("content") == expected["content"]:
            cursor += 1
    return cursor == len(history)


def _protocol_is_valid(messages: list[Any]) -> tuple[bool, list[str], str]:
    assistant_ids: list[str] = []
    tool_ids: list[str] = []
    tool_texts: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        if message.get("role") == "assistant":
            for call in message.get("tool_calls") or []:
                if isinstance(call, dict) and isinstance(call.get("id"), str):
                    assistant_ids.append(call["id"])
        if message.get("role") == "tool":
            if isinstance(message.get("tool_call_id"), str):
                tool_ids.append(message["tool_call_id"])
            tool_texts.append(str(message.get("content", "")))
    valid = bool(assistant_ids) and assistant_ids == tool_ids
    return valid, assistant_ids, "\n".join(tool_texts)


def _usage_is_complete(result: dict[str, Any]) -> bool:
    usage = result.get("usage")
    return (
        isinstance(usage, dict)
        and isinstance(usage.get("prompt_tokens"), int)
        and usage["prompt_tokens"] > 0
        and isinstance(usage.get("completion_tokens"), int)
        and usage["completion_tokens"] > 0
        and isinstance(usage.get("requests"), int)
        and usage["requests"] > 0
    )


def _credential_free(payload: Any, extra_env: dict[str, str] | None) -> bool:
    text = json.dumps(payload, ensure_ascii=False)
    if re.search(r"\bsk-[A-Za-z0-9_-]{12,}\b", text):
        return False
    for name, value in (extra_env or {}).items():
        if "KEY" in name and value and len(value) >= 8 and value in text:
            return False
    return True


def _audit_case(
    case: dict[str, Any],
    *,
    process_ok: bool,
    result: dict[str, Any],
    elapsed_s: float,
    extra_env: dict[str, str] | None,
) -> dict[str, Any]:
    expected = case["expected"]
    answer = str(result.get("answer", ""))
    messages = result.get("messages")
    messages_list = messages if isinstance(messages, list) else []
    protocol_valid, tool_call_ids, tool_text = _protocol_is_valid(messages_list)
    expected_failed_ids = list(expected.get("failed_ids") or [])
    expected_evidence = list(expected.get("evidence") or [])
    checks = {
        "process_exit_zero": process_ok,
        "agent_reported_ok": result.get("ok") is True,
        "answer_has_expected_decision": expected["decision"].casefold() in answer.casefold(),
        "answer_has_required_content": _contains_all(
            answer, list(expected.get("answer_substrings") or [])
        ),
        "answer_avoids_forbidden_content": not any(
            value.casefold() in answer.casefold()
            for value in expected.get("forbidden_answer_substrings") or []
        ),
        "standard_tool_protocol": protocol_valid,
        "tool_result_has_expected_decision": expected["decision"].casefold()
        in tool_text.casefold(),
        "tool_result_covers_failed_ids": _contains_all(tool_text, expected_failed_ids),
        "tool_result_covers_evidence": _contains_all(tool_text, expected_evidence),
        "history_preserved": _history_is_preserved(messages_list, case.get("history") or []),
        "context_used_in_answer": _contains_all(
            answer, list(expected.get("context_markers") or [])
        ),
        "provider_usage_present": _usage_is_complete(result),
        "raw_evidence_credential_free": _credential_free(result, extra_env),
    }
    return {
        "id": case["id"],
        "kind": case["kind"],
        "task": case["task"],
        "history": case.get("history") or [],
        "expected": expected,
        "process_elapsed_s": elapsed_s,
        "checks": checks,
        "score": sum(checks.values()),
        "max_score": len(checks),
        "passed": all(checks.values()),
        "tool_call_ids": tool_call_ids,
        "raw_result": result,
    }


def validate_agent(
    root: Path,
    *,
    live_task: str | None = None,
    live_cases: list[dict[str, Any]] | None = None,
    model: str | None = None,
    timeout: int = 180,
    extra_env: dict[str, str] | None = None,
) -> ValidationReport:
    started = time.perf_counter()
    structural_ok, errors = _structural_check(root)
    compile_ok, compile_output, _compile_s = _run(
        [sys.executable, "-m", "compileall", "-q", "agent.py", "domain_tools.py", "main.py"],
        root,
        timeout,
        extra_env,
    )
    if not compile_ok:
        errors.append(f"compile failed:\n{compile_output}")
    tests_ok, test_output, _test_s = _run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        root,
        timeout,
        extra_env,
    )
    if not tests_ok:
        errors.append(f"tests failed:\n{test_output}")

    cases = list(live_cases or [])
    if live_task is not None and not cases:
        cases = [
            {
                "id": "diagnostic_live_task",
                "kind": "basic_task",
                "history": [],
                "task": live_task,
                "expected": {
                    "decision": "",
                    "failed_ids": [],
                    "evidence": [],
                    "answer_substrings": [],
                    "forbidden_answer_substrings": [],
                    "context_markers": [],
                },
            }
        ]

    audited_cases: list[dict[str, Any]] = []
    if cases and structural_ok and compile_ok and tests_ok:
        for case in cases:
            command = [sys.executable, "main.py", "--task", case["task"]]
            if model:
                command += ["--model", model]
            history = case.get("history") or []
            command += ["--history-json", json.dumps(history, ensure_ascii=False)]
            process_ok, output, elapsed_s = _run(command, root, timeout, extra_env)
            try:
                result = json.loads(output)
                if not isinstance(result, dict):
                    raise ValueError("CLI result must be an object")
            except (json.JSONDecodeError, ValueError) as exc:
                result = {
                    "ok": False,
                    "answer": "",
                    "raw_stdout": output,
                    "parse_error": f"{type(exc).__name__}: {exc}",
                }
            audited = _audit_case(
                case,
                process_ok=process_ok,
                result=result,
                elapsed_s=elapsed_s,
                extra_env=extra_env,
            )
            audited_cases.append(audited)
            if not audited["passed"]:
                failed = [name for name, value in audited["checks"].items() if not value]
                errors.append(f"live case {case['id']} failed checks: {', '.join(failed)}")
    elif cases:
        errors.append("live cases skipped because deterministic gates failed")

    live_requested = bool(cases)
    live_ok = all(case["passed"] for case in audited_cases) and len(audited_cases) == len(cases) if live_requested else None
    protocol_ok = all(case["checks"]["standard_tool_protocol"] for case in audited_cases) if live_requested else None
    state_cases = [case for case in audited_cases if case["kind"] == "multi_turn_state"]
    multiturn_ok = (
        bool(state_cases)
        and all(
            case["checks"]["history_preserved"] and case["checks"]["context_used_in_answer"]
            for case in state_cases
        )
        if live_requested
        else None
    )
    raw_evidence_ok = all(
        case["checks"]["raw_evidence_credential_free"] for case in audited_cases
    ) if live_requested else None
    usage_ok = all(case["checks"]["provider_usage_present"] for case in audited_cases) if live_requested else None
    quality_score = sum(case["score"] for case in audited_cases)
    quality_max = sum(case["max_score"] for case in audited_cases)
    live_result = audited_cases[0]["raw_result"] if len(audited_cases) == 1 else None
    return ValidationReport(
        structural_ok=structural_ok,
        compile_ok=compile_ok,
        tests_ok=tests_ok,
        live_ok=live_ok,
        protocol_ok=protocol_ok,
        multiturn_ok=multiturn_ok,
        raw_evidence_ok=raw_evidence_ok,
        usage_ok=usage_ok,
        semantic_ok=live_ok,
        duration_s=round(time.perf_counter() - started, 3),
        errors=errors,
        live_result=live_result,
        live_cases=audited_cases,
        quality_score=quality_score,
        quality_max_score=quality_max,
    )
