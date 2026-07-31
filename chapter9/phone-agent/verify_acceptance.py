#!/usr/bin/env python3
"""Fail-closed verification for a saved Experiment 9-2 acceptance run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUIRED_ARTIFACTS = {"direct.json", "react.json", "comparison.json", "server.log"}
REQUIRED_SOURCES = {
    "book/chapter9.md",
    "chapter9/README.md",
    "chapter9/phone-agent/README.md",
    "chapter9/phone-agent/agent.py",
    "chapter9/phone-agent/demo.py",
    "chapter9/phone-agent/direct_call.py",
    "chapter9/phone-agent/env.example",
    "chapter9/phone-agent/requirements.txt",
    "chapter9/phone-agent/run_acceptance.py",
    "chapter9/phone-agent/static/app.js",
    "chapter9/phone-agent/static/index.html",
    "chapter9/phone-agent/static/style.css",
    "chapter9/phone-agent/test_agent.py",
    "chapter9/phone-agent/test_webrtc_app.py",
    "chapter9/phone-agent/verify_acceptance.py",
    "chapter9/phone-agent/webrtc_app.py",
    "pyproject.toml",
    "uv.lock",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} is not a JSON object")
    return value


def check_arm(name: str, record: dict[str, Any], failures: list[str]) -> None:
    prefix = f"{name}: "
    transport = record.get("transport") or {}
    stats = transport.get("rtc_stats") or {}
    acceptance = record.get("acceptance") or {}
    checks = acceptance.get("checks") or {}
    transcript = record.get("transcript") or []
    completion = record.get("completion") or {}
    expected = {
        "sdp_offer_answer_negotiated",
        "ice_connected",
        "data_channel_open",
        "local_microphone_track",
        "remote_audio_track",
        "outbound_audio_rtp",
        "inbound_audio_rtp",
        "server_consumed_microphone_audio",
        "user_turn_recorded",
        "agent_turn_recorded",
        "critical_fields_extracted",
    }
    if record.get("experiment") != "9-2" or record.get("mode") != name or record.get("status") != "completed":
        failures.append(prefix + "identity/mode/status mismatch")
    if transport.get("kind") != "webrtc" or transport.get("pstn_used") is not False:
        failures.append(prefix + "transport is not non-PSTN WebRTC")
    if transport.get("e164_required") is not False:
        failures.append(prefix + "E.164 was incorrectly required")
    if not transport.get("sdp_negotiated"):
        failures.append(prefix + "SDP was not negotiated")
    for field in ("offer_sha256", "answer_sha256"):
        digest = str(transport.get(field) or "")
        if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
            failures.append(prefix + f"invalid {field}")
    if transport.get("ice_connected_observed") is not True:
        failures.append(prefix + "ICE was not connected")
    if not transport.get("data_channel_open") or not transport.get("local_audio_track") or not transport.get(
        "remote_audio_track"
    ):
        failures.append(prefix + "data channel or audio track gate failed")
    for field in ("inbound_packets", "inbound_bytes", "outbound_packets", "outbound_bytes"):
        if not isinstance(stats.get(field), int) or stats[field] <= 0:
            failures.append(prefix + f"non-positive RTC stat {field}")
    if not isinstance(transport.get("server_received_audio_frames"), int) or transport["server_received_audio_frames"] <= 0:
        failures.append(prefix + "server consumed no microphone frames")
    if record.get("errors"):
        failures.append(prefix + "runtime errors were retained")
    speakers = {turn.get("speaker") for turn in transcript if isinstance(turn, dict) and turn.get("text")}
    if not {"agent", "user"}.issubset(speakers):
        failures.append(prefix + "two-sided transcript is absent")
    if not completion.get("appointment_time") or not completion.get("confirmation_number"):
        failures.append(prefix + "critical fields were not extracted")
    if acceptance.get("passed") is not True or set(checks) != expected or not all(checks.values()):
        failures.append(prefix + "acceptance did not pass the exact fail-closed gate set")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    failures: list[str] = []
    try:
        manifest = load_json(run_dir / "manifest.json")
        direct = load_json(run_dir / "direct.json")
        react = load_json(run_dir / "react.json")
        comparison = load_json(run_dir / "comparison.json")

        if set(manifest.get("artifact_sha256", {})) != REQUIRED_ARTIFACTS:
            failures.append("manifest does not enumerate the exact required artifacts")
        if set(manifest.get("source_sha256", {})) != REQUIRED_SOURCES:
            failures.append("manifest does not enumerate the exact required source set")
        for relative, expected in manifest.get("source_sha256", {}).items():
            path = ROOT / relative
            if not path.is_file() or sha256(path) != expected:
                failures.append(f"source hash mismatch: {relative}")
        for relative, expected in manifest.get("artifact_sha256", {}).items():
            path = run_dir / relative
            if not path.is_file() or sha256(path) != expected:
                failures.append(f"artifact hash mismatch: {relative}")

        check_arm("direct", direct, failures)
        check_arm("react", react, failures)
        if direct.get("call_id") == react.get("call_id"):
            failures.append("the two arms reused one call ID")
        if direct.get("input_contract", {}).get("fields_supplied_by_caller") != [
            "callee_name",
            "goal",
            "context",
            "instructions",
        ]:
            failures.append("direct arm did not require all four fixed parameters")
        if react.get("input_contract", {}).get("fields_supplied_by_caller") != ["task"]:
            failures.append("ReAct arm accepted more than the natural-language task")
        if not react.get("plan", {}).get("missing_information"):
            failures.append("ReAct arm did not identify missing information")
        if [step.get("stage") for step in react.get("plan", {}).get("trace", [])] != [
            "observation",
            "reason",
            "action",
        ]:
            failures.append("ReAct trace is not observation/reason/action")
        comparison_checks = comparison.get("checks") or {}
        if comparison.get("passed") is not True or not comparison_checks or not all(comparison_checks.values()):
            failures.append("direct-vs-ReAct comparison did not pass every check")
        if manifest.get("result") != "passed" or manifest.get("execution") != "live_local_aiortc_webrtc":
            failures.append("manifest result/execution mismatch")
        if manifest.get("pstn_used") is not False or manifest.get("credentials_saved") is not False:
            failures.append("manifest violates PSTN/credential boundary")
        if manifest.get("environment", {}).get("media_peer") != "aiortc":
            failures.append("manifest does not identify the aiortc media peer")
        for arm, record in (("direct", direct), ("react", react)):
            if manifest.get("acceptance", {}).get(arm) != record.get("acceptance"):
                failures.append(f"manifest {arm} acceptance does not match the raw record")
        if manifest.get("acceptance", {}).get("comparison_passed") is not True:
            failures.append("manifest comparison gate is false")
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"malformed or incomplete evidence: {exc}")

    result = {"run_id": run_dir.name, "passed": not failures, "failures": failures}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
