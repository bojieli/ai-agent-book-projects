#!/usr/bin/env python3
"""Pinned, fail-closed launcher and receipt writer for Experiment 9-8."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

COMMIT = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"
AUTHORIZATION = "I_AUTHORIZE_XLEROBOT_TELEOPERATION"
MODES = {
    "keyboard": ("software/examples/4_xlerobot_teleop_keyboard.py", "efbe076dfbda3c6280fa54f0eb5bca1a12518a0d"),
    "xbox": ("software/examples/5_xlerobot_teleop_xbox.py", "de7bc17d570167e58b15e38c06c0fa23af74632a"),
    "joycon": ("software/examples/7_xlerobot_teleop_joycon.py", "21a48258d22b1fc002f63555a2f3dc2950bdfb24"),
    "vr": ("software/examples/8_xlerobot_teleop_vr.py", "315bb81f13a37746de0f329e3ba11240a2230806"),
}


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--mode", choices=sorted(MODES), required=True)
    parser.add_argument("--receipt", type=Path, help="JSON receipt path; required for --execute")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization-token", default="")
    parser.add_argument("--operator")
    parser.add_argument("--robot-calibrated", action="store_true")
    parser.add_argument("--clear-workspace", action="store_true")
    parser.add_argument("--emergency-stop-ready", action="store_true")
    parser.add_argument("--human-observer-present", action="store_true")
    args = parser.parse_args()

    entrypoint, blob = MODES[args.mode]
    source = args.upstream / entrypoint
    source_commit = git(args.upstream, "rev-parse", "HEAD")
    source_blob = git(args.upstream, "rev-parse", f"HEAD:{entrypoint}")
    config = {
        "experiment_id": "9-8",
        "mode": args.mode,
        "upstream": str(args.upstream.resolve()),
        "commit": source_commit,
        "entrypoint": entrypoint,
        "entrypoint_blob": source_blob,
        "command": [sys.executable, str(source.resolve())],
        "actuation_requested": args.execute,
    }
    print(json.dumps(config, indent=2))
    if source_commit != COMMIT or source_blob != blob or not source.is_file():
        parser.error("the checkout or selected entrypoint does not match upstream.lock.json")
    if not args.execute:
        print("DRY CONFIG ONLY: no device was opened and no motion was attempted.")
        return 0

    required = {
        "authorization token": args.authorization_token == AUTHORIZATION,
        "receipt path": args.receipt is not None,
        "identified operator": bool(args.operator),
        "robot calibration": args.robot_calibrated,
        "clear workspace": args.clear_workspace,
        "emergency stop": args.emergency_stop_ready,
        "human observer": args.human_observer_present,
    }
    missing = [name for name, present in required.items() if not present]
    if missing:
        parser.error("refusing actuation; missing: " + ", ".join(missing))

    started = datetime.now(timezone.utc).isoformat()
    command = [sys.executable, str(source.resolve())]
    env = os.environ.copy()
    extra_paths = [str((args.upstream / "software").resolve()), str((args.upstream / "XLeVR").resolve())]
    env["PYTHONPATH"] = os.pathsep.join(extra_paths + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    log_path = args.receipt.with_suffix(".log")
    return_code = 1
    error: str | None = None
    try:
        with log_path.open("w", encoding="utf-8") as log:
            log.write("command=" + shlex.join(command) + "\n")
            log.flush()
            result = subprocess.run(command, cwd=args.upstream, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
            return_code = result.returncode
    except Exception as exc:  # preserve direct failure evidence
        error = f"{type(exc).__name__}: {exc}"
    receipt = {
        **config,
        "kind": "direct_execution_receipt",
        "started_at": started,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "operator": args.operator,
        "host": platform.node() or "unknown",
        "actuation_authorized": True,
        "safety": {
            "robot_calibrated": args.robot_calibrated,
            "clear_workspace": args.clear_workspace,
            "emergency_stop_ready": args.emergency_stop_ready,
            "human_observer_present": args.human_observer_present,
        },
        "return_code": return_code,
        "error": error,
        "log_path": str(log_path),
        "log_sha256": sha256(log_path) if log_path.is_file() else None,
        "completed_process": error is None,
    }
    write_json(args.receipt, receipt)
    print(f"receipt={args.receipt} sha256={sha256(args.receipt)}")
    return return_code if error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
