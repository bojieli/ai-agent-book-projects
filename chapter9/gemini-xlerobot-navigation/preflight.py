#!/usr/bin/env python3
"""Read-only preflight for the pinned Experiment 9-9 reproduction track."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

COMMIT = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"
GUIDE = "docs/en/source/software/getting_started/LLM_agent.md"
GUIDE_BLOB = "d336a9e35838267614d31cdb98b9b50d66427f03"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True, text=True).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--camera", type=Path, default=Path("/dev/camera_center"), help="checked by path only")
    parser.add_argument("--serial-port", type=Path, default=Path("/dev/arm_right"), help="checked by path only")
    parser.add_argument("--safety-checklist-complete", action="store_true")
    parser.add_argument("--api-validation", type=Path, help="saved output from plan_saved_frame.py proving exact-model access")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks: list[dict[str, object]] = []

    def add(check_id: str, passed: bool, detail: str, required: bool = True) -> None:
        checks.append({"id": check_id, "passed": passed, "required_for_hardware_run": required, "detail": detail})

    head = git(args.upstream, "rev-parse", "HEAD")
    add("pinned_commit", head == COMMIT, f"expected {COMMIT}; found {head or 'not a git checkout'}")
    guide_blob = git(args.upstream, "rev-parse", f"HEAD:{GUIDE}")
    add("pinned_guide", guide_blob == GUIDE_BLOB, f"expected {GUIDE_BLOB}; found {guide_blob or 'missing'}")
    robocrew_found = importlib.util.find_spec("robocrew") is not None
    version = None
    if robocrew_found:
        try:
            version = importlib.metadata.version("robocrew")
        except importlib.metadata.PackageNotFoundError:
            pass
    add("robocrew_0_3_1", version == "0.3.1", f"found {version or 'not installed'}")
    key_alias = "GEMINI_API_KEY" if os.environ.get("GEMINI_API_KEY") else "GOOGLE_API_KEY" if os.environ.get("GOOGLE_API_KEY") else None
    add("gemini_api_key", bool(key_alias), f"present via {key_alias} (value not read)" if key_alias else "neither GEMINI_API_KEY nor GOOGLE_API_KEY is set")
    api_record = None
    if args.api_validation and args.api_validation.is_file():
        try:
            api_record = json.loads(args.api_validation.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            api_record = None
    api_access = bool(
        api_record
        and api_record.get("status") == "complete"
        and api_record.get("model") == "gemini-robotics-er-1.5-preview"
        and api_record.get("api_call_attempted") is True
        and api_record.get("actuation_attempted") is False
    )
    api_detail = "not supplied"
    if args.api_validation:
        api_detail = f"{args.api_validation}: " + (f"status={api_record.get('status')}" if api_record else "unreadable")
    add("exact_model_access", api_access, api_detail)
    add("camera_path", args.camera.exists(), f"{args.camera}: {'exists' if args.camera.exists() else 'missing'}")
    add("serial_path", args.serial_port.exists(), f"{args.serial_port}: {'exists' if args.serial_port.exists() else 'missing'}")
    add("safety_checklist", args.safety_checklist_complete, "operator attestation present" if args.safety_checklist_complete else "not attested")

    blockers = [str(item["id"]) for item in checks if item["required_for_hardware_run"] and not item["passed"]]
    report = {
        "schema_version": "1.0",
        "experiment_id": "9-9",
        "kind": "non_actuating_preflight",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": platform.node() or "unknown",
        "upstream_path": str(args.upstream.resolve()),
        "required_model": "gemini-robotics-er-1.5-preview",
        "status": "ready" if not blockers else "blocked",
        "checks": checks,
        "blockers": blockers,
        "api_call_attempted": False,
        "actuation_attempted": False
    }
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        print(rendered, end="")
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
