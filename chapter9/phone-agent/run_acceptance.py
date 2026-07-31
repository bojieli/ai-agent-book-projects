#!/usr/bin/env python3
"""Run and package the canonical direct-vs-ReAct WebRTC acceptance.

This is not a mock transport. Headless Chrome negotiates two genuine WebRTC
sessions with the local aiortc peer, publishes synthetic microphone RTP from
Chrome's test device, receives connection audio RTP, and uses the WebRTC data
channel for the scripted participant turns. No PSTN destination is contacted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_request(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read())


def wait_for(check: Callable[[], Any], timeout: float, label: str) -> Any:
    deadline = time.monotonic() + timeout
    last: Any = None
    while time.monotonic() < deadline:
        try:
            last = check()
            if last:
                return last
        except (urllib.error.URLError, json.JSONDecodeError):
            pass
        time.sleep(0.5)
    raise TimeoutError(f"timed out waiting for {label}; last={last!r}")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def chrome_path() -> str:
    candidates = [
        os.getenv("CHROME_PATH", ""),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome") or "",
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError("Chrome/Chromium was not found; set CHROME_PATH")


def run_arm(page: Page, base_url: str, arm: str) -> dict[str, Any]:
    page.goto(base_url, wait_until="networkidle")
    page.check(f'input[name="mode"][value="{arm}"]')
    if arm == "direct":
        page.fill("#callee-name", "Jane Doe")
        page.fill("#goal", "Collect and confirm Jane Doe's preferred dental-checkup time.")
        page.fill("#context", "Tuesday afternoon from 2pm to 4pm is available; the user will supply a confirmation code.")
        page.fill(
            "#instructions",
            "Ask for one exact time and a confirmation code. Repeat both, ask for confirmation, then call "
            "complete_task with only those confirmed details.",
        )
        reply = "Tuesday at 3pm works. I explicitly confirm it, with confirmation code WEBRTC-DIRECT-92."
    else:
        page.fill(
            "#task",
            "Call me to arrange a dental checkup for Jane Doe. I forgot to include a time and confirmation "
            "code, so ask me for both, repeat my choice, and save only what I confirm.",
        )
        reply = "Tuesday at 3pm works. I explicitly confirm it, with confirmation code WEBRTC-REACT-92."

    page.click("#start")
    page.wait_for_function(
        "() => window.exp92?.state?.dc?.readyState === 'open' && "
        "['connected','completed'].includes(window.exp92.state.pc.iceConnectionState)",
        timeout=90_000,
    )
    call_id = page.locator("#call-id").inner_text()
    wait_for(
        lambda: any(turn["speaker"] == "agent" for turn in json_request(f"{base_url}/api/calls/{call_id}")["transcript"]),
        90,
        f"{arm} opening audio transcript",
    )
    page.evaluate("async (text) => await window.exp92.sendText(text)", reply)

    def completed() -> dict[str, Any] | None:
        record = json_request(f"{base_url}/api/calls/{call_id}")
        return record if record["completion"] else None

    try:
        wait_for(completed, 75, f"{arm} complete_task")
    except TimeoutError:
        page.evaluate(
            "async (text) => await window.exp92.sendText(text)",
            "Yes. That is my final explicit confirmation. Save the time and confirmation code now.",
        )
        wait_for(completed, 75, f"{arm} complete_task after confirmation")

    wait_for(
        lambda: (
            (record := json_request(f"{base_url}/api/calls/{call_id}"))["transport"]["rtc_stats"]["inbound_packets"] > 0
            and record["transport"]["rtc_stats"]["outbound_packets"] > 0
        ),
        45,
        f"{arm} bidirectional RTP counters",
    )
    record = page.evaluate("async () => await window.exp92.hangup('automated_acceptance')")
    if not record["acceptance"]["passed"]:
        raise AssertionError(f"{arm} acceptance failed: {record['acceptance']}")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Run directory (default: timestamped under validation/runs)")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (args.output or HERE / "validation" / "runs" / f"exp9-2-webrtc-{stamp}").resolve()
    output.mkdir(parents=True, exist_ok=False)
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    server_log = output / "server.log"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Pin the canonical result to the dependency-free planner/dialogue path.
    # Readers may opt into a hosted provider, but media never depends on one.
    env["PHONE_MODEL_PROVIDER"] = "local"
    with server_log.open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "webrtc_app:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=HERE,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_for(lambda: json_request(base_url + "/api/health").get("ok"), 30, "local server")
            executable = chrome_path()
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=executable,
                    headless=True,
                    args=[
                        "--use-fake-ui-for-media-stream",
                        "--use-fake-device-for-media-stream",
                        "--autoplay-policy=no-user-gesture-required",
                        "--no-default-browser-check",
                    ],
                )
                context = browser.new_context(permissions=["microphone"])
                direct = run_arm(context.new_page(), base_url, "direct")
                react = run_arm(context.new_page(), base_url, "react")
                context.close()
                browser.close()
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)

    comparison_checks = {
        "same_webrtc_transport": direct["transport"]["kind"] == react["transport"]["kind"] == "webrtc",
        "no_pstn_or_e164": (
            not direct["transport"]["pstn_used"]
            and not react["transport"]["pstn_used"]
            and not direct["transport"]["e164_required"]
            and not react["transport"]["e164_required"]
        ),
        "direct_required_fixed_parameters": direct["input_contract"]["fields_supplied_by_caller"]
        == ["callee_name", "goal", "context", "instructions"],
        "react_accepted_only_natural_language_task": react["input_contract"]["fields_supplied_by_caller"] == ["task"],
        "react_detected_missing_information": bool(react["plan"]["missing_information"]),
        "react_has_observe_reason_act_trace": [step["stage"] for step in react["plan"]["trace"]]
        == ["observation", "reason", "action"],
        "react_planner_recorded_model": bool(react["plan"]["planner_model"]),
        "direct_full_stack_passed": direct["acceptance"]["passed"],
        "react_full_stack_passed": react["acceptance"]["passed"],
        "both_extracted_critical_fields": bool(direct["completion"]) and bool(react["completion"]),
    }
    comparison = {
        "schema_version": 1,
        "experiment": "9-2",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "control": "direct fixed-parameter WebRTC call",
        "treatment": "natural-language task -> ReAct plan -> WebRTC call",
        "checks": comparison_checks,
        "passed": all(comparison_checks.values()),
        "conclusion": (
            "Both arms completed real bidirectional browser-to-aiortc WebRTC media sessions. The direct arm required four "
            "pre-filled parameters; the ReAct arm accepted one incomplete natural-language task, identified "
            "missing facts, collected them during the call, and saved the confirmed fields."
        ),
    }
    if not comparison["passed"]:
        raise AssertionError(f"comparison failed: {comparison_checks}")

    artifacts = {"direct.json": direct, "react.json": react, "comparison.json": comparison}
    for name, value in artifacts.items():
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sources = [
        HERE / "agent.py",
        HERE / "webrtc_app.py",
        HERE / "run_acceptance.py",
        HERE / "verify_acceptance.py",
        HERE / "demo.py",
        HERE / "direct_call.py",
        HERE / "env.example",
        HERE / "requirements.txt",
        HERE / "test_agent.py",
        HERE / "test_webrtc_app.py",
        HERE / "static" / "index.html",
        HERE / "static" / "app.js",
        HERE / "static" / "style.css",
        HERE / "README.md",
        ROOT / "chapter9" / "README.md",
        ROOT / "book" / "chapter9.md",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
    ]
    executable = Path(chrome_path())
    manifest = {
        "schema_version": 1,
        "experiment": "9-2",
        "run_id": output.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "passed",
        "execution": "live_local_aiortc_webrtc",
        "pstn_used": False,
        "credentials_saved": False,
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "chrome_version": subprocess.check_output([str(executable), "--version"], text=True).strip(),
            "chrome_executable_sha256": sha256(executable),
            "planner_model": react["plan"]["planner_model"],
            "direct_dialogue_models": direct["models"]["dialogue_models"],
            "react_dialogue_models": react["models"]["dialogue_models"],
            "media_peer": "aiortc",
        },
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in sources},
        "artifact_sha256": {
            **{name: sha256(output / name) for name in artifacts},
            "server.log": sha256(server_log),
        },
        "acceptance": {
            "direct": direct["acceptance"],
            "react": react["acceptance"],
            "comparison_passed": comparison["passed"],
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run_dir": str(output), "passed": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
