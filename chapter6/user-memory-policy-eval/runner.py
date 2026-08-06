#!/usr/bin/env python3
"""Real-API trajectory-prefix evaluation for user-memory policy use.

The experiment deliberately supplies the memory to the model.  It does not
measure whether a retriever found a fact; it measures whether the next action
uses, scopes, overrides, or refuses that known fact correctly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from openai import OpenAI


HERE = Path(__file__).resolve().parent
DEFAULT_CASES = HERE / "cases.json"
DEFAULT_OUTPUT = HERE / "results" / "policy_prefix_live.json"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


class APIClient:
    def __init__(self, model: str, timeout: float = 120.0):
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is required for the live experiment")
        self.model = model
        self.client = OpenAI(api_key=key, base_url=OPENROUTER_BASE_URL, timeout=timeout)

    def json_call(self, system: str, user: str) -> tuple[dict[str, Any], str, Usage]:
        last_error: Exception | None = None
        for attempt in range(3):
            started = time.perf_counter()
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=0,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content or "{}"
                usage = getattr(response, "usage", None)
                observed = Usage(
                    input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
                    output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
                return parse_json(raw), raw, observed
            except Exception as exc:  # provider errors are retained by the caller
                last_error = exc
                if attempt < 2:
                    time.sleep(2**attempt)
        raise RuntimeError(f"OpenRouter call failed for {self.model}: {last_error}") from last_error


def parse_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {"parse_error": "model did not return a JSON object", "raw": raw}
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {"parse_error": "embedded JSON was invalid", "raw": raw}
    return value if isinstance(value, dict) else {"parse_error": "JSON value was not an object", "raw": raw}


def memory_text(memory: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(memory, ensure_ascii=False, indent=2)
    if fmt == "markdown":
        return "\n".join(
            [
                f"### Memory {memory['id']}",
                f"- fact: {memory['fact']}",
                f"- scope: {memory['scope']}",
                f"- applies_when: {'；'.join(memory['applies_when'])}",
                f"- avoid_when: {'；'.join(memory['avoid_when'])}",
                f"- confidence: {memory['confidence']}",
                f"- source: {memory['source']}",
            ]
        )
    if fmt == "python":
        def quote(value: Any) -> str:
            return repr(value)

        return "\n".join(
            [
                "# Data only; do not execute this memory.",
                "memory = {",
                f"    'id': {quote(memory['id'])},",
                f"    'fact': {quote(memory['fact'])},",
                f"    'scope': {quote(memory['scope'])},",
                f"    'applies_when': {quote(memory['applies_when'])},",
                f"    'avoid_when': {quote(memory['avoid_when'])},",
                f"    'confidence': {quote(memory['confidence'])},",
                f"    'source': {quote(memory['source'])},",
                "}",
            ]
        )
    raise ValueError(f"unsupported memory format: {fmt}")


SYSTEM_PROMPT = """You are an enterprise general Agent evaluating whether to use a known user memory.
The memory is evidence and a scoped default, never an unconditional command.
Priority order: current explicit user instruction, authoritative current environment or repository rules, current task context, then scoped long-term memory.
If the scope is unclear or a high-impact action is irreversible, inspect or ask before acting.
Do not invent facts. Return ONLY a JSON object with these fields:
{
  "decision": "apply|ignore|override|ask|inspect|confirm|follow_environment|follow_current_instruction|neutral",
  "memory_ids_used": ["..."],
  "next_step_type": "answer|ask_user|inspect_repo_policy|follow_repo_policy|commit_main|create_worktree|open_pull_request|publish|ask_confirmation|inspect_dependencies|delete_files|bulk_cleanup|answer_json|answer_markdown|apply_memory|neutral",
  "next_step": "one concise observable next action or answer",
  "rationale": "brief explanation grounded in the supplied memory and current state"
}
"""


def build_user_prompt(case: dict[str, Any], fmt: str) -> str:
    return "\n".join(
        [
            "Known long-term memory (the model has already received it):",
            memory_text(case["memory"], fmt),
            "",
            "Trajectory prefix:",
            case["trajectory_prefix"],
            "",
            f"Current task: {case['current_task']}",
            f"Environment and tool state: {case['environment']}",
            "Decide the next observable action. Apply the memory only if its scope fits this task.",
        ]
    )


def contains_term(value: str, term: str) -> bool:
    return term.casefold() in value.casefold()


def score(case: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    decision = str(parsed.get("decision", "")).strip()
    next_type = str(parsed.get("next_step_type", "")).strip()
    next_step = str(parsed.get("next_step", ""))
    used = parsed.get("memory_ids_used", [])
    if not isinstance(used, list):
        used = []
    used_ids = {str(item) for item in used}
    memory_id = case["memory"]["id"]

    decision_ok = decision in set(expected["accepted_decisions"])
    next_type_ok = next_type in set(expected["allowed_next_step_types"])
    required_text = " ".join([next_step, str(parsed.get("rationale", ""))])
    required_ok = all(contains_term(required_text, term) for term in expected.get("required_terms", []))
    forbidden_ok = next_type not in set(expected.get("forbidden_next_step_types", []))
    usage_mode = expected["memory_usage"]
    if usage_mode == "must_use":
        usage_ok = memory_id in used_ids
    elif usage_mode == "must_not_use":
        usage_ok = memory_id not in used_ids
    else:
        usage_ok = True
    passed = all([decision_ok, next_type_ok, required_ok, forbidden_ok, usage_ok])
    return {
        "decision_ok": decision_ok,
        "next_step_type_ok": next_type_ok,
        "required_terms_ok": required_ok,
        "forbidden_next_step_ok": forbidden_ok,
        "memory_usage_ok": usage_ok,
        "passed": passed,
        "observed_decision": decision,
        "observed_next_step_type": next_type,
        "observed_memory_ids": sorted(used_ids),
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cases_path: Path, output: Path, model: str, formats: list[str], max_cases: int | None) -> dict[str, Any]:
    source = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = source["cases"][:max_cases] if max_cases else source["cases"]
    client = APIClient(model)
    records: list[dict[str, Any]] = []
    for fmt in formats:
        for index, case in enumerate(cases, start=1):
            print(f"[{fmt}] {index}/{len(cases)} {case['id']}", flush=True)
            try:
                parsed, raw, usage = client.json_call(SYSTEM_PROMPT, build_user_prompt(case, fmt))
                evaluation = score(case, parsed)
                records.append(
                    {
                        "case_id": case["id"],
                        "suite": case["suite"],
                        "source_signal": case["source_signal"],
                        "failure_class": case["failure_class"],
                        "memory_format": fmt,
                        "model": model,
                        "parsed": parsed,
                        "raw_response": raw,
                        "evaluation": evaluation,
                        "usage": asdict(usage),
                        "status": "ok",
                    }
                )
            except Exception as exc:
                records.append(
                    {
                        "case_id": case["id"],
                        "suite": case["suite"],
                        "source_signal": case["source_signal"],
                        "failure_class": case["failure_class"],
                        "memory_format": fmt,
                        "model": model,
                        "status": "error",
                        "error": str(exc),
                    }
                )

    by_format: dict[str, Any] = {}
    for fmt in formats:
        rows = [row for row in records if row["memory_format"] == fmt]
        ok_rows = [row for row in rows if row["status"] == "ok"]
        by_format[fmt] = {
            "cells": len(rows),
            "successful_api_calls": len(ok_rows),
            "api_errors": len(rows) - len(ok_rows),
            "pass": sum(bool(row.get("evaluation", {}).get("passed")) for row in ok_rows),
            "pass_rate": (sum(bool(row.get("evaluation", {}).get("passed")) for row in ok_rows) / len(ok_rows)) if ok_rows else None,
            "by_failure_class": {
                name: {
                    "pass": sum(bool(row.get("evaluation", {}).get("passed")) for row in ok_rows if row["failure_class"] == name),
                    "total": sum(1 for row in ok_rows if row["failure_class"] == name),
                }
                for name in sorted({row["failure_class"] for row in ok_rows})
            },
        }

    report = {
        "experiment": "6-5",
        "title": "Known-memory policy use on trajectory prefixes",
        "model": model,
        "memory_formats": formats,
        "source_cases": (
            str(cases_path.relative_to(HERE))
            if cases_path.is_relative_to(HERE)
            else str(cases_path)
        ),
        "case_sha256": sha256(cases_path),
        "case_count": len(cases),
        "records": records,
        "summary": {"by_format": by_format},
        "limitations": [
            "The cases are synthetic but derived from production-shaped bad-case categories.",
            "A prefix decision test is diagnostic and does not replace end-to-end task replay.",
            "The deterministic scorer checks observable policy actions; it does not claim to score hidden reasoning.",
            "A single model and three text encodings are not a universal ranking of memory architectures.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output_resolved = output.resolve()
    report_ref = (
        str(output_resolved.relative_to(HERE))
        if output_resolved.is_relative_to(HERE)
        else output.name
    )
    manifest = {
        "experiment": "6-5",
        "report": report_ref,
        "report_sha256": sha256(output),
        "runner": Path(__file__).name,
        "runner_sha256": sha256(Path(__file__)),
        "cases": cases_path.name,
        "case_sha256": sha256(cases_path),
        "model": model,
        "formats": formats,
        "records": len(records),
        "api_errors": sum(row.get("status") == "error" for row in records),
    }
    manifest_path = output.with_name("manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the live user-memory policy prefix evaluation")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default=os.getenv("MEMORY_POLICY_MODEL", "openai/gpt-5.6-sol"))
    parser.add_argument("--formats", nargs="+", choices=["json", "markdown", "python"], default=["json", "markdown", "python"])
    parser.add_argument("--max-cases", type=int, default=None, help="Use a bounded smoke subset; omit for the complete campaign")
    args = parser.parse_args()
    report = run(args.cases, args.output, args.model, args.formats, args.max_cases)
    for fmt, summary in report["summary"]["by_format"].items():
        print(f"{fmt}: {summary['pass']}/{summary['successful_api_calls']} passed; errors={summary['api_errors']}")


if __name__ == "__main__":
    main()
