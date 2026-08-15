"""Validate a retained open-model Computer Use run without another model call."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from evidence import sha256_file, write_json, write_manifest

SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}", re.IGNORECASE),
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: Any) -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def verify_existing_manifest(run_dir: Path) -> tuple[bool, dict[str, Any]]:
    manifest = load_json(run_dir / "manifest.json")
    expected = {item["path"]: item for item in manifest["artifacts"]}
    actual_paths = {
        path.relative_to(run_dir).as_posix()
        for path in run_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    failures = []
    for relative, item in expected.items():
        path = run_dir / relative
        if not path.is_file():
            failures.append({"path": relative, "reason": "missing"})
        elif path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            failures.append({"path": relative, "reason": "hash_or_size_mismatch"})
    extras = sorted(actual_paths - set(expected))
    return not failures and not extras, {"failures": failures, "unmanifested_files": extras}


def credential_scan(run_dir: Path) -> list[dict[str, str]]:
    findings = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(
                    {"path": path.relative_to(run_dir).as_posix(), "pattern": pattern.pattern}
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--latest", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.expanduser().resolve()

    checks: list[dict[str, Any]] = []
    manifest_ok, manifest_detail = verify_existing_manifest(run_dir)
    add_check(checks, "existing_manifest_integrity", manifest_ok, manifest_detail)

    summary = load_json(run_dir / "summary.json")
    history = load_json(run_dir / "history.json")["history"]
    receipts = load_json(run_dir / "api-receipts.json")
    screenshots = load_json(run_dir / "screenshots.json")

    requested_model = summary["api"]["requested_model"]
    response_models = sorted(
        {
            item["body"]["model"]
            for item in receipts
            if item.get("kind") == "response"
            and isinstance(item.get("body"), dict)
            and isinstance(item["body"].get("model"), str)
        }
    )
    requests = [item for item in receipts if item.get("kind") == "request"]
    responses = [item for item in receipts if item.get("kind") == "response"]
    add_check(
        checks,
        "open_model_identity",
        requested_model == "qwen/qwen3-vl-32b-instruct" and response_models == [requested_model],
        {"requested": requested_model, "provider_reported": response_models},
    )
    add_check(
        checks,
        "real_api_receipts",
        len(requests) == len(responses) == len(history)
        and all(item.get("status_code") == 200 for item in responses),
        {"requests": len(requests), "responses": len(responses), "steps": len(history)},
    )

    action_names = []
    one_action_per_step = True
    for item in history:
        actions = (item.get("model_output") or {}).get("action") or []
        one_action_per_step = one_action_per_step and len(actions) <= 1
        for action in actions:
            action_names.extend(action.keys())
    allowed_actions = {"navigate", "input", "click", "wait", "done"}
    add_check(
        checks,
        "bounded_read_only_actions",
        one_action_per_step and set(action_names) <= allowed_actions,
        {"one_action_per_step": one_action_per_step, "actions": action_names},
    )
    add_check(
        checks,
        "completed_within_limit",
        summary["status"] == "complete"
        and summary["agent_reported_success"] is True
        and len(history) == summary["steps_executed"]
        and len(history) <= summary["max_steps"],
        {
            "status": summary["status"],
            "steps": len(history),
            "limit": summary["max_steps"],
        },
    )

    final_observation = history[-1].get("state_message") or ""
    required_observation_fragments = (
        "San Francisco Weather",
        "64\nSunny",
        "Feels Like\n62",
        "High\n74",
        "Low\n55",
        "Chance of Rain\n3%",
    )
    missing_fragments = [item for item in required_observation_fragments if item not in final_observation]
    add_check(
        checks,
        "answer_grounded_in_final_browser_observation",
        not missing_fragments
        and "64°F" in (summary.get("final_result") or "")
        and "sunny" in (summary.get("final_result") or "").lower(),
        {
            "missing_observation_fragments": missing_fragments,
            "final_screenshot": screenshots[-1].get("path"),
            "final_screenshot_sha256": screenshots[-1].get("sha256"),
        },
    )
    retained_screenshots = [item for item in screenshots if item.get("path")]
    screenshot_hashes_ok = all(
        sha256_file(run_dir / item["path"]) == item["sha256"] for item in retained_screenshots
    )
    add_check(
        checks,
        "step_screenshots_retained",
        len(retained_screenshots) == summary["screenshots_retained"] and screenshot_hashes_ok,
        {"retained": len(retained_screenshots), "hashes_ok": screenshot_hashes_ok},
    )

    findings = credential_scan(run_dir)
    add_check(checks, "credential_scan", not findings, {"findings": findings})

    source_root = Path(__file__).resolve().parent
    runtime_sources = ["config.py", "evidence.py", "main.py", "requirements.txt"]
    write_json(
        run_dir / "source-snapshot.json",
        {
            "capture_scope": "post-run hashes of unchanged runtime files",
            "sources": [
                {
                    "path": relative,
                    "bytes": (source_root / relative).stat().st_size,
                    "sha256": sha256_file(source_root / relative),
                }
                for relative in runtime_sources
            ],
        },
    )

    passed = all(item["passed"] for item in checks)
    acceptance_path = run_dir / "acceptance.json"
    write_json(
        acceptance_path,
        {
            "schema_version": 1,
            "experiment": "9-7",
            "arm": "open-model-api",
            "status": "passed" if passed else "failed",
            "checks": checks,
            "qualification": (
                "The Qwen3-VL browser arm passed. This does not claim that the separate "
                "Anthropic native-computer-tool arm in Experiment 9-6 ran."
            ),
        },
    )
    manifest_path = write_manifest(
        run_dir,
        {
            "experiment": "9-7",
            "arm": "open-model-api",
            "status": "passed" if passed else "failed",
            "api": summary["api"],
            "credential_retained": False,
        },
    )
    if args.latest:
        write_json(
            args.latest,
            {
                "schema_version": 1,
                "experiment": "9-7",
                "arm": "open-model-api",
                "status": "passed" if passed else "failed",
                "run_dir": str(run_dir.relative_to(args.latest.parent.resolve())),
                "acceptance_sha256": sha256_file(acceptance_path),
                "manifest_sha256": sha256_file(manifest_path),
            },
        )
    print(json.dumps({"status": "passed" if passed else "failed", "checks": checks}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
