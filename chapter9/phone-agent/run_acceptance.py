#!/usr/bin/env python3
"""Run the safe, full-audio direct-vs-ReAct Experiment 9-2 campaign.

Each arm gives Chrome a non-private synthesized microphone WAV.  Chrome sends that
fixture through getUserMedia and RTP to aiortc; the server buffers the received RTP
audio, runs real Whisper ASR, invokes a real external dialogue model, synthesizes the
Agent's speech, and transmits it on the downlink RTP track.  No semantic user text is
sent over the data channel and no PSTN destination is contacted.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
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
from speech import make_synthetic_speech_fixture, sha256_file

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANONICAL_MODEL = "doubao-seed-1-6-flash-250615"


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


def require_canonical_runtime() -> None:
    if not os.getenv("ARK_API_KEY"):
        raise RuntimeError("canonical acceptance requires ARK_API_KEY")
    whisper_python = os.getenv("WHISPER_PYTHON", sys.executable)
    if not whisper_python or not Path(whisper_python).is_file():
        raise RuntimeError("canonical acceptance requires explicit WHISPER_PYTHON")
    check = subprocess.run(
        [whisper_python, "-c", "import torch, whisper"],
        capture_output=True,
        timeout=30,
        check=False,
    )
    if check.returncode != 0:
        raise RuntimeError("WHISPER_PYTHON cannot import torch and whisper")
    if not shutil.which("ffmpeg") or not (shutil.which("say") or shutil.which("espeak")):
        raise RuntimeError("canonical acceptance requires ffmpeg and say/espeak")


def _arm_request(page: Page, arm: str) -> None:
    page.check(f'input[name="mode"][value="{arm}"]')
    if arm == "direct":
        page.fill("#callee-name", "Jane Doe")
        page.fill(
            "#goal",
            "Collect and confirm Jane Doe's preferred dental-checkup time and confirmation code.",
        )
        page.fill(
            "#context",
            "Tuesday afternoon from 2pm to 4pm is available; the user must supply the exact time and code by voice.",
        )
        page.fill(
            "#instructions",
            "Ask for one exact time and a confirmation code. Repeat both, require explicit confirmation, then call "
            "complete_task with only the ASR-confirmed details.",
        )
    else:
        page.fill(
            "#task",
            "Call me to arrange a dental checkup for Jane Doe. I forgot to include the exact time and confirmation "
            "code, so identify both as missing, ask me for them by voice, and save only what I explicitly confirm.",
        )


def run_arm(page: Page, base_url: str, arm: str, fixture_duration: float) -> dict[str, Any]:
    page.goto(base_url, wait_until="networkidle")
    _arm_request(page, arm)
    page.click("#start")
    page.wait_for_function(
        "() => window.exp92?.state?.dc?.readyState === 'open' && "
        "['connected','completed'].includes(window.exp92.state.pc.iceConnectionState)",
        timeout=120_000,
    )
    call_id = page.locator("#call-id").inner_text()

    def record() -> dict[str, Any]:
        return json_request(f"{base_url}/api/calls/{call_id}")

    wait_for(
        lambda: (
            (value := record())["models"]["tts_receipts"]
            and value["models"]["tts_receipts"][0].get("delivery_complete")
        ),
        120,
        f"{arm} synthesized opening speech on downlink RTP",
    )
    # The fake device starts at getUserMedia.  Wait through its one-shot safe
    # fixture before sending a control-only commit event.
    page.wait_for_timeout(int((fixture_duration + 1.0) * 1000))
    page.evaluate("async () => await window.exp92.commitAudio()")

    def completion_or_error() -> dict[str, Any] | None:
        value = record()
        return value if value.get("completion") or value.get("errors") else None

    completed = wait_for(completion_or_error, 300, f"{arm} microphone ASR -> LLM -> completion")
    if completed["errors"]:
        raise AssertionError(f"{arm} runtime errors: {completed['errors']}")
    wait_for(
        lambda: (
            (value := record())["models"]["tts_receipts"]
            and len(value["models"]["tts_receipts"]) >= 2
            and all(item.get("delivery_complete") for item in value["models"]["tts_receipts"])
        ),
        180,
        f"{arm} all Agent TTS transmitted on downlink RTP",
    )
    page.evaluate("async () => await window.exp92.collectStats()")
    wait_for(
        lambda: (
            (value := record())["transport"]["rtc_stats"]["inbound_packets"] > 0
            and value["transport"]["rtc_stats"]["outbound_packets"] > 0
        ),
        45,
        f"{arm} bidirectional RTP counters",
    )
    final = page.evaluate("async () => await window.exp92.hangup('automated_safe_acceptance')")
    if not final["acceptance"]["passed"]:
        raise AssertionError(f"{arm} acceptance failed: {final['acceptance']}")
    return final


def _credential_scan(paths: list[Path]) -> dict[str, Any]:
    secrets = [
        secret.encode()
        for name, secret in os.environ.items()
        if any(marker in name.upper() for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD"))
        and len(secret) >= 8
    ]
    failures = []
    for path in paths:
        data = path.read_bytes()
        if any(secret in data for secret in secrets):
            failures.append(str(path))
    return {
        "scanned_file_count": len(paths),
        "environment_credential_value_matches": failures,
        "passed": not failures,
    }


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "not-installed"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, help="Run directory (default: timestamped under validation/runs)"
    )
    args = parser.parse_args()
    require_canonical_runtime()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = (
        args.output or HERE / "validation" / "runs" / f"exp9-2-webrtc-audio-{stamp}"
    ).resolve()
    output.mkdir(parents=True, exist_ok=False)

    fixture_text = {
        "direct": (
            "Tuesday at three P M works. The confirmation code is Maple seven. "
            "I explicitly confirm Tuesday at three P M and confirmation code Maple seven."
        ),
        "react": (
            "Tuesday at three P M works. The confirmation code is Cedar eight. "
            "I explicitly confirm Tuesday at three P M and confirmation code Cedar eight."
        ),
    }
    fixtures: dict[str, dict[str, Any]] = {}
    fixture_paths: dict[str, Path] = {}
    for arm, text in fixture_text.items():
        path = output / "fixtures" / f"{arm}_microphone.wav"
        fixtures[arm] = make_synthetic_speech_fixture(text, path)
        fixtures[arm]["artifact_path"] = str(path.relative_to(output))
        fixtures[arm]["text_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        fixture_paths[arm] = path

    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    server_log = output / "server.log"
    env = dict(os.environ)
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PHONE_MODEL_PROVIDER": "ark",
            "PHONE_PLANNER_MODEL": CANONICAL_MODEL,
            "PHONE_DIALOGUE_MODEL": CANONICAL_MODEL,
            "PHONE_TTS_ENGINE": "say" if shutil.which("say") else "espeak",
            "WHISPER_MODEL": "tiny",
            "WHISPER_PYTHON": os.getenv("WHISPER_PYTHON", sys.executable),
            "PHONE_SAFE_SYNTHETIC_ACCEPTANCE": "1",
            "PHONE_EVIDENCE_DIR": str(output),
        }
    )
    server_cleaned = False
    browsers_closed = False
    with server_log.open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "webrtc_app:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=HERE,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            health = wait_for(lambda: json_request(base_url + "/api/health"), 45, "local server")
            if not health.get("model_credential_present"):
                raise RuntimeError("server did not observe the model credential")
            executable = chrome_path()
            with sync_playwright() as playwright:
                records: dict[str, dict[str, Any]] = {}
                for arm in ("direct", "react"):
                    browser = playwright.chromium.launch(
                        executable_path=executable,
                        headless=True,
                        args=[
                            "--use-fake-ui-for-media-stream",
                            "--use-fake-device-for-media-stream",
                            f"--use-file-for-fake-audio-capture={fixture_paths[arm]}%noloop",
                            "--autoplay-policy=no-user-gesture-required",
                            "--no-default-browser-check",
                        ],
                    )
                    context = browser.new_context(permissions=["microphone"])
                    try:
                        records[arm] = run_arm(
                            context.new_page(),
                            base_url,
                            arm,
                            float(fixtures[arm]["duration_seconds"]),
                        )
                    finally:
                        context.close()
                        browser.close()
                browsers_closed = True
        finally:
            server.terminate()
            try:
                server.wait(timeout=15)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            server_cleaned = server.poll() is not None

    direct = records["direct"]
    react = records["react"]
    comparison_checks = {
        "same_browser_aiortc_webrtc_transport": direct["transport"]["kind"]
        == react["transport"]["kind"]
        == "webrtc",
        "no_pstn_or_e164": all(
            record["transport"]["pstn_used"] is False
            and record["transport"]["e164_required"] is False
            for record in (direct, react)
        ),
        "direct_required_fixed_parameters": direct["input_contract"]["fields_supplied_by_caller"]
        == ["callee_name", "goal", "context", "instructions"],
        "react_accepted_only_natural_language_task": react["input_contract"][
            "fields_supplied_by_caller"
        ]
        == ["task"],
        "react_detected_missing_information": bool(react["plan"]["missing_information"]),
        "react_has_observe_reason_act_trace": [step["stage"] for step in react["plan"]["trace"]]
        == ["observation", "reason", "action"],
        "react_used_real_external_planner": any(
            item["purpose"] == "react_planning" and item["execution"] == "real_external_llm"
            for item in react["models"]["llm_receipts"]
        ),
        "both_used_microphone_rtp_asr": all(
            record["models"]["asr_receipts"][0]["input_source"] == "browser_microphone_rtp"
            for record in (direct, react)
        ),
        "both_used_real_downlink_tts": all(
            len(record["models"]["tts_receipts"]) >= 2
            and all(item["delivery_complete"] for item in record["models"]["tts_receipts"])
            for record in (direct, react)
        ),
        "both_used_external_post_asr_dialogue": all(
            any(item["purpose"] == "post_asr_dialogue" for item in record["models"]["llm_receipts"])
            for record in (direct, react)
        ),
        "data_channel_never_supplied_user_semantics": all(
            record["event_counts"].get("semantic_user_messages", 0) == 0
            for record in (direct, react)
        ),
        "both_completed_all_audio_gates": direct["acceptance"]["passed"]
        and react["acceptance"]["passed"],
        "both_saved_confirmed_structured_fields": all(
            record["completion"]["appointment_time"] and record["completion"]["confirmation_number"]
            for record in (direct, react)
        ),
    }
    comparison = {
        "schema_version": 2,
        "experiment": "9-2",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "control": "fixed parameters -> browser microphone RTP -> ASR -> real LLM dialogue -> TTS RTP",
        "treatment": "natural task -> real LLM ReAct plan -> browser microphone RTP -> ASR -> real LLM dialogue -> TTS RTP",
        "checks": comparison_checks,
        "passed": all(comparison_checks.values()),
        "conclusion": (
            "Both arms completed the same real bidirectional browser/aiortc audio path. The treatment additionally "
            "used an external ARK ReAct planning receipt to detect missing facts; the control used fixed parameters."
        ),
    }
    if not comparison["passed"]:
        raise AssertionError(f"comparison failed: {comparison_checks}")

    artifacts = {"direct.json": direct, "react.json": react, "comparison.json": comparison}
    for name, value in artifacts.items():
        (output / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    source_paths = [
        HERE / "agent.py",
        HERE / "speech.py",
        HERE / "webrtc_app.py",
        HERE / "run_acceptance.py",
        HERE / "verify_acceptance.py",
        HERE / "demo.py",
        HERE / "direct_call.py",
        HERE / "env.example",
        HERE / "requirements.txt",
        HERE / "test_agent.py",
        HERE / "test_speech.py",
        HERE / "test_webrtc_app.py",
        HERE / "test_verify_acceptance.py",
        HERE / "static" / "index.html",
        HERE / "static" / "app.js",
        HERE / "static" / "style.css",
        HERE / "README.md",
        ROOT / "chapter9" / "README.md",
        ROOT / "book" / "chapter9.md",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
    ]
    evidence_files = sorted(path for path in output.rglob("*") if path.is_file())
    scan = _credential_scan(evidence_files)
    if not scan["passed"]:
        raise RuntimeError(
            f"credential values found in evidence: {scan['environment_credential_value_matches']}"
        )
    executable = Path(chrome_path())
    manifest = {
        "schema_version": 2,
        "experiment": "9-2",
        "run_id": output.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "passed",
        "execution": "live_browser_aiortc_asr_external_llm_tts_webrtc",
        "canonical_safe_synthetic_fixture": True,
        "pstn_used": False,
        "e164_required": False,
        "credentials_saved": False,
        "private_audio_or_transcripts_saved": False,
        "safe_fixture_provenance": fixtures,
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "chrome_version": subprocess.check_output(
                [str(executable), "--version"], text=True
            ).strip(),
            "chrome_executable_sha256": sha256_file(executable),
            "planner_provider": "ark",
            "planner_model": CANONICAL_MODEL,
            "dialogue_model": CANONICAL_MODEL,
            "media_peer": "aiortc",
            "packages": {
                "aiortc": _package_version("aiortc"),
                "av": _package_version("av"),
                "openai": _package_version("openai"),
                "playwright": _package_version("playwright"),
            },
        },
        "source_sha256": {str(path.relative_to(ROOT)): sha256_file(path) for path in source_paths},
        "artifact_sha256": {
            str(path.relative_to(output)): sha256_file(path) for path in evidence_files
        },
        "redaction": scan,
        "cleanup": {
            "browser_contexts_closed": browsers_closed,
            "server_process_terminated": server_cleaned,
            "raw_private_media_created": False,
        },
        "acceptance": {
            "direct": direct["acceptance"],
            "react": react["acceptance"],
            "comparison_passed": comparison["passed"],
        },
    }
    if (
        manifest["cleanup"]["browser_contexts_closed"] is not True
        or manifest["cleanup"]["server_process_terminated"] is not True
        or manifest["cleanup"]["raw_private_media_created"] is not False
    ):
        raise AssertionError(f"cleanup gate failed: {manifest['cleanup']}")
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"run_dir": str(output), "passed": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
