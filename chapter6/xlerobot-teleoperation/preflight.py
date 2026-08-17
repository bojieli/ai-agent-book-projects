#!/usr/bin/env python3
"""Read-only preflight for the pinned Experiment 6-10 reproduction track."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

COMMIT = "3d14695e40c9c68229c0aacffca6053c75cd3eb6"
PINNED_BLOBS = {
    "docs/en/source/software/getting_started/XLeRobot_teleop.md": "3992358282ff54cfce8d90a525e784aedcf045f7",
    "software/examples/4_xlerobot_teleop_keyboard.py": "efbe076dfbda3c6280fa54f0eb5bca1a12518a0d",
    "software/examples/5_xlerobot_teleop_xbox.py": "de7bc17d570167e58b15e38c06c0fa23af74632a",
    "software/examples/7_xlerobot_teleop_joycon.py": "21a48258d22b1fc002f63555a2f3dc2950bdfb24",
    "software/examples/8_xlerobot_teleop_vr.py": "315bb81f13a37746de0f329e3ba11240a2230806",
}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True, text=True).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, required=True, help="local checkout of Vector-Wangel/XLeRobot")
    parser.add_argument("--serial-port", action="append", default=[], help="expected robot serial device; checked by path only")
    parser.add_argument("--safety-checklist-complete", action="store_true", help="operator attests calibration, clear workspace, observer, and E-stop")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    checks: list[dict[str, object]] = []

    def add(check_id: str, passed: bool, detail: str, required: bool = True) -> None:
        checks.append({"id": check_id, "passed": passed, "required_for_hardware_run": required, "detail": detail})

    head = git(args.upstream, "rev-parse", "HEAD")
    add("pinned_commit", head == COMMIT, f"expected {COMMIT}; found {head or 'not a git checkout'}")
    for path, blob in PINNED_BLOBS.items():
        found = git(args.upstream, "rev-parse", f"HEAD:{path}")
        add(f"blob:{path}", found == blob, f"expected {blob}; found {found or 'missing'}")
    for module in ("numpy", "pygame", "lerobot", "joyconrobotics"):
        found = importlib.util.find_spec(module) is not None
        add(f"python_module:{module}", found, "installed" if found else "not importable")
    add("serial_ports_supplied", bool(args.serial_port), "no serial ports supplied" if not args.serial_port else ", ".join(args.serial_port))
    for device in args.serial_port:
        add(f"device:{device}", Path(device).exists(), "path exists" if Path(device).exists() else "path missing")
    add("safety_checklist", args.safety_checklist_complete, "operator attestation present" if args.safety_checklist_complete else "not attested")

    blockers = [str(item["id"]) for item in checks if item["required_for_hardware_run"] and not item["passed"]]
    report = {
        "schema_version": "1.0",
        "experiment_id": "6-10",
        "kind": "non_actuating_preflight",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": platform.node() or "unknown",
        "upstream_path": str(args.upstream.resolve()),
        "status": "ready" if not blockers else "blocked",
        "checks": checks,
        "blockers": blockers,
        "actuation_attempted": False,
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
