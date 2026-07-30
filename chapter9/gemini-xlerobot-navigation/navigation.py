#!/usr/bin/env python3
"""Fail-closed runner for the exact Experiment 9-9 navigation configuration."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

MODEL = "google_genai:gemini-robotics-er-1.5-preview"
TASK = "find the kitchen and go there"
AUTHORIZATION = "I_AUTHORIZE_XLEROBOT_MOTION"


def configuration(args: argparse.Namespace) -> dict[str, object]:
    return {
        "model": MODEL,
        "task": TASK,
        "camera": str(args.camera),
        "right_arm_wheel_usb": str(args.right_arm_wheel_usb),
        "camera_fov_degrees": 90,
        "angular_overlay": True,
        "tools": ["move_forward", "turn_left", "turn_right"],
        "target_decision_frequency_hz": [0.5, 1.0],
        "actuation_requested": args.execute,
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=Path, default=Path("/dev/camera_center"))
    parser.add_argument("--right-arm-wheel-usb", type=Path, default=Path("/dev/arm_right"))
    parser.add_argument("--execute", action="store_true", help="allow the program to reach RoboCrew's actuation loop")
    parser.add_argument("--authorization-token", default="", help="must exactly match the token documented in README")
    parser.add_argument("--operator")
    parser.add_argument("--receipt", type=Path, help="JSON receipt path; required for --execute")
    parser.add_argument("--robot-calibrated", action="store_true")
    parser.add_argument("--clear-route", action="store_true")
    parser.add_argument("--emergency-stop-ready", action="store_true")
    parser.add_argument("--human-observer-present", action="store_true")
    args = parser.parse_args()
    print(json.dumps(configuration(args), indent=2))
    if not args.execute:
        print("DRY CONFIG ONLY: no API call, device access, or motion was attempted.")
        return 0
    if args.authorization_token != AUTHORIZATION:
        parser.error("--execute requires the exact explicit authorization token")
    required = {
        "identified operator": bool(args.operator),
        "receipt path": args.receipt is not None,
        "robot calibration": args.robot_calibrated,
        "clear route": args.clear_route,
        "emergency stop": args.emergency_stop_ready,
        "human observer": args.human_observer_present,
    }
    missing = [name for name, present in required.items() if not present]
    if missing:
        parser.error("refusing actuation; missing: " + ", ".join(missing))
    if not os.environ.get("GOOGLE_API_KEY"):
        parser.error("GOOGLE_API_KEY is required")
    try:
        robocrew_version = importlib.metadata.version("robocrew")
    except importlib.metadata.PackageNotFoundError:
        parser.error("robocrew==0.3.1 is required")
    if robocrew_version != "0.3.1":
        parser.error(f"robocrew==0.3.1 is required; found {robocrew_version}")
    for label, path in (("camera", args.camera), ("right-arm wheel controller", args.right_arm_wheel_usb)):
        if not path.exists():
            parser.error(f"{label} path does not exist: {path}")

    # Deliberately import hardware/API dependencies only after every fail-closed gate.
    from robocrew.core.camera import RobotCamera
    from robocrew.core.LLMAgent import LLMAgent
    from robocrew.robots.XLeRobot.servo_controls import ServoControler
    from robocrew.robots.XLeRobot.tools import create_move_forward, create_turn_left, create_turn_right

    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    log_path = args.receipt.with_suffix(".log")
    started = datetime.now(timezone.utc).isoformat()
    error: str | None = None
    finished = False
    try:
        with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            camera = RobotCamera(str(args.camera))
            controller = ServoControler(right_arm_wheel_usb=str(args.right_arm_wheel_usb))
            tools = [
                create_move_forward(controller),
                create_turn_left(controller),
                create_turn_right(controller),
            ]
            agent = LLMAgent(
                model=MODEL,
                tools=tools,
                main_camera=camera,
                camera_fov=90,
                servo_controler=controller,
                debug_mode=True,
            )
            agent.task = TASK
            agent.go()
            finished = True
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    receipt = {
        **configuration(args),
        "kind": "direct_execution_receipt",
        "started_at": started,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "operator": args.operator,
        "host": platform.node() or "unknown",
        "safety": {
            "robot_calibrated": args.robot_calibrated,
            "clear_route": args.clear_route,
            "emergency_stop_ready": args.emergency_stop_ready,
            "human_observer_present": args.human_observer_present,
        },
        "agent_go_returned": finished,
        "error": error,
        "log_path": str(log_path),
        "log_sha256": sha256(log_path) if log_path.is_file() else None,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"receipt={args.receipt} sha256={sha256(args.receipt)}")
    return 0 if finished else 1


if __name__ == "__main__":
    raise SystemExit(main())
