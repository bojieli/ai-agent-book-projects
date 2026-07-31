#!/usr/bin/env python3
"""Run the complete safe Experiment 10-5 acceptance scenario.

The form and its submission endpoint are localhost-only.  Synthetic personal data is
spoken by the configured TTS provider, crosses a real WebRTC audio track, is recorded
at the remote peer, and goes through the configured ASR provider.  It is not injected
as text.  One deliberately invalid email proves validation feedback and re-asking.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar
from urllib.parse import parse_qs

import demo
from validate_acceptance import validate_run

FORM_HTML = """<!doctype html>
<html lang="en"><meta charset="utf-8"><title>Safe local registration</title>
<h1>Conference registration</h1>
<form method="post" action="/register">
  <label for="firstName">First name</label>
  <input id="firstName" name="firstName" required>
  <label for="lastName">Last name</label>
  <input id="lastName" name="lastName" required>
  <label for="email">Email address</label>
  <input id="email" name="email" type="email" required placeholder="name@example.com">
  <label for="userNumber">Phone number</label>
  <input id="userNumber" name="userNumber" type="tel" required pattern="[0-9]{10}" title="10 digits">
  <label for="gender">Gender</label>
  <select id="gender" name="gender" required>
    <option value="">Choose one</option><option>Female</option><option>Male</option><option>Non-binary</option>
  </select>
  <label for="address">Mailing address</label>
  <textarea id="address" name="address" required></textarea>
  <button type="submit">Register</button>
</form></html>"""


ANSWERS = {
    "firstName": "Alice",
    "lastName": "Tan",
    "email": ["This is not an email address", "alice@example.com"],
    "userNumber": "9123456789",
    "gender": "Female",
    "address": "One Example Street, Singapore",
}

CREDENTIAL_PATTERN = re.compile(
    r"(?i)(?:sk-[A-Za-z0-9_-]{12,}|gho_[A-Za-z0-9_-]{12,}|"
    r"github_pat_[A-Za-z0-9_-]{12,}|authorization.{0,16}bearer\s+[A-Za-z0-9._-]{12,})"
)


class _AcceptanceFormHandler(BaseHTTPRequestHandler):
    submissions: ClassVar[list[dict[str, object]]] = []

    def do_GET(self):
        if self.path != "/register":
            self.send_error(404)
            return
        body = FORM_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/register":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        parsed = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        self.__class__.submissions.append(
            {
                "field_names": sorted(parsed),
                "field_count": len(parsed),
                "all_values_redacted": True,
            }
        )
        body = b"registration accepted by local test endpoint"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_values() -> list[str]:
    values = []
    for answer in ANSWERS.values():
        if isinstance(answer, list):
            values.extend(str(item) for item in answer)
        else:
            values.append(str(answer))
    # Select options such as "Female" legitimately appear in the page observation
    # before the participant answers; they are public schema, not collected PII.
    return [value for value in values if value and value not in FORM_HTML]


def _has_credential(value: str) -> bool:
    return bool(CREDENTIAL_PATTERN.search(value))


async def _git_head(root: Path) -> str:
    process = await asyncio.create_subprocess_exec(
        "git",
        "rev-parse",
        "HEAD",
        cwd=root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"git rev-parse HEAD failed: {stderr.decode('utf-8').strip()}")
    return stdout.decode("utf-8").strip()


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Safe full acceptance for Experiment 10-5")
    p.add_argument(
        "--run-dir", default=None, help="output directory (default: timestamped validation run)"
    )
    return p


async def run(run_dir: Path) -> int:
    run_dir.mkdir(parents=True, exist_ok=False)
    _AcceptanceFormHandler.submissions = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _AcceptanceFormHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/register"
    report_path = run_dir / "acceptance_report.json"
    decision_path = run_dir / "decision.json"
    timeline_path = run_dir / "message_timeline.json"
    receipt_path = run_dir / "form_submission_receipt.json"
    raw_request_path = run_dir / "raw_decision_request.json"
    raw_response_path = run_dir / "raw_decision_response.json"
    input_path = run_dir / "experiment_input.json"
    validation_report_path = run_dir / "validation_report.json"
    experiment_input = {
        "schema_version": 1,
        "experiment": "10-5",
        "page_url": url,
        "form_html": FORM_HTML,
        "form_html_sha256": hashlib.sha256(FORM_HTML.encode("utf-8")).hexdigest(),
        "field_answer_counts": {
            name: len(value) if isinstance(value, list) else 1 for name, value in ANSWERS.items()
        },
        "participant": "safe synthesized voice over WebRTC RTP",
        "participant_values_retained": False,
    }
    input_path.write_text(
        json.dumps(experiment_input, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    try:
        args = demo.parser().parse_args(
            [
                "--url",
                url,
                "--headless",
                "--submit",
                "--phone-transport",
                "webrtc",
                "--webrtc-headless",
                "--confirm-consent",
                "--webrtc-answers-json",
                json.dumps(ANSWERS),
                "--trace",
                str(timeline_path),
                "--decision-trace",
                str(decision_path),
                "--raw-decision-request",
                str(raw_request_path),
                "--raw-decision-response",
                str(raw_response_path),
                "--acceptance-report",
                str(report_path),
            ]
        )
        exit_code = await demo.main(args)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    receipt = {
        "endpoint_scope": "localhost-only",
        "submission_count": len(_AcceptanceFormHandler.submissions),
        "submissions": _AcceptanceFormHandler.submissions,
        "raw_values_retained": False,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    submission_pass = bool(
        exit_code == 0
        and receipt["submission_count"] == 1
        and receipt["submissions"][0]["field_count"] == len(ANSWERS)
        and set(receipt["submissions"][0]["field_names"]) == set(ANSWERS)
    )
    report["safe_local_submission_receipt"] = receipt
    report["gates"]["real_form_submission"] = {
        "status": "pass" if submission_pass else "fail",
        "reason": None
        if submission_pass
        else "localhost endpoint did not receive exactly one complete submission",
    }
    persisted = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (report_path, decision_path, timeline_path, receipt_path)
    )
    value_leak = any(value in persisted for value in _synthetic_values())
    credential_leak = _has_credential(persisted)
    privacy_pass = bool(
        report["gates"]["privacy_redaction_and_ephemeral_audio"]["status"] == "pass"
        and not value_leak
        and not credential_leak
    )
    report["gates"]["privacy_redaction_and_ephemeral_audio"] = {
        "status": "pass" if privacy_pass else "fail",
        "reason": None if privacy_pass else "retained artifacts failed the credential/value scan",
    }
    all_gates_pass = all(item["status"] == "pass" for item in report["gates"].values())
    report["overall_status"] = "pass" if all_gates_pass else "incomplete"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    root = Path(__file__).parent
    git_head = await _git_head(root)
    runtime_files = [
        "browser.py",
        "bus.py",
        "decision.py",
        "demo.py",
        "models.py",
        "orchestration.py",
        "run_acceptance.py",
        "validate_acceptance.py",
        "voice.py",
        "webrtc_channel.py",
    ]
    artifacts = [
        report_path,
        decision_path,
        timeline_path,
        receipt_path,
        raw_request_path,
        raw_response_path,
    ]
    manifest = {
        "schema_version": 2,
        "experiment": "10-5",
        "run_kind": "full_safe_webrtc_acceptance",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "git_head_at_run": git_head,
        "command": "python run_acceptance.py --run-dir <validation-run-directory>",
        "providers": {
            "decision_and_extraction": report["decision_provider"],
            "speech": report["webrtc_receipt"]["speech_provider"],
        },
        "privacy": {
            "phone_number_required": False,
            "pstn_provider_required": False,
            "participant": "safe synthesized voice",
            "raw_audio_retained": False,
            "transcripts_or_values_retained": False,
            "form_values_retained": False,
        },
        "source_sha256": {name: sha256(root / name) for name in runtime_files},
        "input_sha256": {input_path.name: sha256(input_path)},
        "artifact_sha256": {path.name: sha256(path) for path in artifacts},
        "acceptance": {
            "overall_status": report["overall_status"],
            "gate_count": len(report["gates"]),
            "passed_gate_count": sum(item["status"] == "pass" for item in report["gates"].values()),
        },
    }
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    validation_report = validate_run(
        run_dir,
        source_root=root,
        require_validation_report=False,
    )
    validation_report_path.write_text(
        json.dumps(validation_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    manifest["artifact_sha256"][validation_report_path.name] = sha256(validation_report_path)
    manifest["retained_evidence_validation"] = validation_report["status"]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    final_validation = validate_run(run_dir, source_root=root)
    if final_validation != validation_report:
        raise RuntimeError("standalone validation result changed after manifest finalization")
    print(
        json.dumps({"run_dir": str(run_dir), "overall_status": report["overall_status"]}, indent=2)
    )
    return 0 if report["overall_status"] == "pass" else 1


if __name__ == "__main__":
    arguments = parser().parse_args()
    destination = (
        Path(arguments.run_dir)
        if arguments.run_dir
        else Path("validation/runs") / ("exp10-5-webrtc-" + time.strftime("%Y%m%dT%H%M%S%z"))
    )
    raise SystemExit(asyncio.run(run(destination)))
