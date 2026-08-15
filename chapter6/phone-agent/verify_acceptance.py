#!/usr/bin/env python3
"""Standalone fail-closed verification for Experiment 9-2 retained evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REQUIRED_ARTIFACTS = {
    "direct.json",
    "react.json",
    "comparison.json",
    "server.log",
    "fixtures/direct_microphone.wav",
    "fixtures/react_microphone.wav",
    "media/direct/agent_01.wav",
    "media/direct/agent_02.wav",
    "media/direct/microphone_rtp_asr_input.wav",
    "media/react/agent_01.wav",
    "media/react/agent_02.wav",
    "media/react/microphone_rtp_asr_input.wav",
}
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
    "chapter9/phone-agent/speech.py",
    "chapter9/phone-agent/static/app.js",
    "chapter9/phone-agent/static/index.html",
    "chapter9/phone-agent/static/style.css",
    "chapter9/phone-agent/test_agent.py",
    "chapter9/phone-agent/test_speech.py",
    "chapter9/phone-agent/test_verify_acceptance.py",
    "chapter9/phone-agent/test_webrtc_app.py",
    "chapter9/phone-agent/verify_acceptance.py",
    "chapter9/phone-agent/webrtc_app.py",
    "pyproject.toml",
    "uv.lock",
}
REQUIRED_ARM_CHECKS = {
    "sdp_offer_answer_negotiated",
    "ice_connected",
    "data_channel_open",
    "browser_microphone_track",
    "server_downlink_audio_track",
    "outbound_audio_rtp",
    "inbound_audio_rtp",
    "server_buffered_microphone_rtp",
    "real_asr_consumed_microphone_audio",
    "external_react_planner_or_fixed_direct_control",
    "real_external_post_asr_dialogue",
    "real_tts_assets_synthesized",
    "tts_audio_transmitted_on_downlink",
    "media_is_canonical_transcript_source",
    "data_channel_is_control_and_caption_only",
    "missing_fields_were_clarified_aloud",
    "explicit_confirmation_observed",
    "structured_completion_saved",
    "no_mock_probe_or_fallback",
    "privacy_boundary_preserved",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name} is not a JSON object")
    return value


def valid_hash(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def check_llm_receipt(receipt: dict[str, Any], prefix: str, failures: list[str]) -> None:
    raw = receipt.get("raw_response") or {}
    request = receipt.get("request") or {}
    choices = raw.get("choices") or []
    usage = receipt.get("usage") or {}
    raw_usage = raw.get("usage") or {}
    content = receipt.get("response_content")
    if (
        receipt.get("execution") != "real_external_llm"
        or receipt.get("external_request_completed") is not True
    ):
        failures.append(prefix + "LLM execution is not a completed external request")
    if (
        receipt.get("mock") is not False
        or receipt.get("probe_only") is not False
        or receipt.get("fallback_used") is not False
    ):
        failures.append(prefix + "LLM receipt permits mock/probe/fallback")
    if receipt.get("credential_fields_retained") is not False:
        failures.append(prefix + "LLM receipt does not assert credential-free retention")
    if not receipt.get("provider_response_id") or receipt.get("provider_response_id") != raw.get(
        "id"
    ):
        failures.append(prefix + "provider response ID is absent or differs from raw response")
    if not receipt.get("provider_model") or receipt.get("provider_model") != raw.get("model"):
        failures.append(prefix + "provider model is absent or differs from raw response")
    if not choices or receipt.get("finish_reason") != choices[0].get("finish_reason"):
        failures.append(prefix + "finish status is absent or differs from raw response")
    raw_content = (choices[0].get("message") or {}).get("content") if choices else None
    if not content or content != raw_content:
        failures.append(prefix + "retained response content differs from raw response")
    if not usage or int(usage.get("total_tokens", 0)) <= 0 or usage != raw_usage:
        failures.append(prefix + "usage is absent or differs from raw response")
    if float(receipt.get("latency_seconds", 0)) <= 0:
        failures.append(prefix + "LLM latency is not positive")
    if receipt.get("request_sha256") != sha256_json(request):
        failures.append(prefix + "LLM request hash mismatch")
    if receipt.get("raw_response_sha256") != sha256_json(raw):
        failures.append(prefix + "LLM raw response hash mismatch")
    if receipt.get("response_content_sha256") != hashlib.sha256(str(content).encode()).hexdigest():
        failures.append(prefix + "LLM response content hash mismatch")
    if request.get("model") != receipt.get("requested_model") or not request.get("messages"):
        failures.append(prefix + "raw request/model is incomplete")


def check_arm(name: str, record: dict[str, Any], run_dir: Path, failures: list[str]) -> None:
    prefix = f"{name}: "
    transport = record.get("transport") or {}
    stats = transport.get("rtc_stats") or {}
    models = record.get("models") or {}
    llm_receipts = models.get("llm_receipts") or []
    asr_receipts = models.get("asr_receipts") or []
    tts_receipts = models.get("tts_receipts") or []
    transcript = record.get("transcript") or []
    completion = record.get("completion") or {}
    acceptance = record.get("acceptance") or {}
    checks = acceptance.get("checks") or {}

    if (
        record.get("experiment") != "9-2"
        or record.get("mode") != name
        or record.get("status") != "completed"
    ):
        failures.append(prefix + "identity/mode/status mismatch")
    if transport.get("kind") != "webrtc" or transport.get("pstn_used") is not False:
        failures.append(prefix + "transport is not non-PSTN WebRTC")
    if transport.get("e164_required") is not False:
        failures.append(prefix + "E.164 was incorrectly required")
    if not transport.get("sdp_negotiated") or not transport.get("ice_connected_observed"):
        failures.append(prefix + "SDP/ICE gate failed")
    for field in ("offer_sha256", "answer_sha256"):
        if not valid_hash(transport.get(field)):
            failures.append(prefix + f"invalid {field}")
    if (
        not transport.get("data_channel_open")
        or not transport.get("local_audio_track")
        or not transport.get("remote_audio_track")
    ):
        failures.append(prefix + "data channel or bidirectional audio-track gate failed")
    for field in ("inbound_packets", "inbound_bytes", "outbound_packets", "outbound_bytes"):
        if not isinstance(stats.get(field), int) or stats[field] <= 0:
            failures.append(prefix + f"non-positive RTC stat {field}")
    if (
        int(transport.get("server_received_audio_frames", 0)) <= 0
        or int(transport.get("server_received_audio_pcm_bytes", 0)) <= 0
    ):
        failures.append(prefix + "server did not buffer microphone RTP audio")
    if record.get("errors"):
        failures.append(prefix + "runtime errors were retained")

    planning = [item for item in llm_receipts if item.get("purpose") == "react_planning"]
    dialogue = [item for item in llm_receipts if item.get("purpose") == "post_asr_dialogue"]
    if name == "direct" and planning:
        failures.append(prefix + "direct control unexpectedly used an LLM planner")
    if name == "react" and len(planning) != 1:
        failures.append(prefix + "ReAct arm lacks exactly one planner receipt")
    if len(dialogue) != 1:
        failures.append(prefix + "arm lacks exactly one post-ASR dialogue receipt")
    for index, receipt in enumerate(llm_receipts):
        check_llm_receipt(receipt, f"{prefix}llm[{index}]: ", failures)

    if len(asr_receipts) != 1:
        failures.append(prefix + "arm lacks exactly one ASR receipt")
    for receipt in asr_receipts:
        artifact = run_dir / str(receipt.get("retained_safe_fixture_path", ""))
        if (
            receipt.get("execution") != "real_local_inference"
            or receipt.get("input_source") != "browser_microphone_rtp"
            or receipt.get("mock") is not False
            or receipt.get("probe_only") is not False
            or receipt.get("fallback_used") is not False
            or not valid_hash(receipt.get("checkpoint_sha256"))
            or not artifact.is_file()
            or sha256(artifact) != receipt.get("input_wav_sha256")
        ):
            failures.append(prefix + "ASR provenance/input artifact gate failed")
        if (
            not receipt.get("transcript")
            or receipt.get("transcript_sha256")
            != hashlib.sha256(str(receipt.get("transcript", "")).encode()).hexdigest()
        ):
            failures.append(prefix + "ASR transcript/hash gate failed")

    if len(tts_receipts) != 2:
        failures.append(prefix + "arm lacks exactly two Agent TTS receipts")
    for index, receipt in enumerate(tts_receipts):
        artifact = run_dir / str(receipt.get("retained_safe_fixture_path", ""))
        if (
            receipt.get("execution") != "real_speech_synthesis"
            or receipt.get("mock") is not False
            or receipt.get("probe_only") is not False
            or receipt.get("fallback_used") is not False
            or not artifact.is_file()
            or sha256(artifact) != receipt.get("wav_sha256")
            or receipt.get("delivery_complete") is not True
            or receipt.get("enqueued_on_webrtc_track") is not True
            or receipt.get("delivered_pcm_sha256") != receipt.get("pcm_sha256")
            or int(receipt.get("transmitted_samples", 0)) != int(receipt.get("sample_count", -1))
        ):
            failures.append(prefix + f"TTS/downlink provenance gate failed at receipt {index}")

    if not transcript or any(
        turn.get("source")
        != ("asr.microphone_rtp" if turn.get("speaker") == "user" else "tts.webrtc_downlink")
        for turn in transcript
    ):
        failures.append(prefix + "canonical transcript contains a non-media semantic source")
    if record.get("event_counts", {}).get("semantic_user_messages", 0) != 0:
        failures.append(prefix + "data channel supplied user semantics")
    if not transcript or transcript[0].get("purpose") != "missing_field_clarification":
        failures.append(prefix + "missing-field clarification was not the first TTS turn")
    if record.get("explicit_confirmation_observed") is not True:
        failures.append(prefix + "explicit confirmation was not observed")
    if (
        not completion.get("appointment_time")
        or not completion.get("confirmation_number")
        or completion.get("tool") != "complete_task"
    ):
        failures.append(prefix + "structured completion fields/tool are incomplete")
    if (
        completion.get("result") != "Local confirmation recorded."
        or completion.get("notes") != "No external organization was contacted or booking made."
    ):
        failures.append(prefix + "structured completion violates the no-external-action boundary")
    privacy = record.get("privacy") or {}
    if (
        privacy.get("safe_synthetic_acceptance") is not True
        or privacy.get("private_audio_retained") is not False
        or privacy.get("private_transcripts_retained") is not False
    ):
        failures.append(prefix + "privacy/safe-fixture boundary mismatch")
    if (
        acceptance.get("passed") is not True
        or set(checks) != REQUIRED_ARM_CHECKS
        or not all(checks.values())
    ):
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

        check_arm("direct", direct, run_dir, failures)
        check_arm("react", react, run_dir, failures)
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
        if (
            comparison.get("passed") is not True
            or not comparison_checks
            or not all(comparison_checks.values())
        ):
            failures.append("direct-vs-ReAct comparison did not pass every check")
        if (
            manifest.get("result") != "passed"
            or manifest.get("execution") != "live_browser_aiortc_asr_external_llm_tts_webrtc"
        ):
            failures.append("manifest result/execution mismatch")
        if (
            manifest.get("canonical_safe_synthetic_fixture") is not True
            or manifest.get("pstn_used") is not False
            or manifest.get("e164_required") is not False
            or manifest.get("credentials_saved") is not False
            or manifest.get("private_audio_or_transcripts_saved") is not False
        ):
            failures.append("manifest violates canonical safety/telephony boundary")
        if manifest.get("environment", {}).get("media_peer") != "aiortc":
            failures.append("manifest does not identify aiortc")
        if manifest.get("redaction", {}).get("passed") is not True:
            failures.append("manifest redaction gate is false")
        cleanup = manifest.get("cleanup") or {}
        if (
            cleanup.get("browser_contexts_closed") is not True
            or cleanup.get("server_process_terminated") is not True
        ):
            failures.append("manifest cleanup gate is false")
        if cleanup.get("raw_private_media_created") is not False:
            failures.append("manifest says private media was created")
        for arm, record in (("direct", direct), ("react", react)):
            if manifest.get("acceptance", {}).get(arm) != record.get("acceptance"):
                failures.append(f"manifest {arm} acceptance differs from raw record")
        if manifest.get("acceptance", {}).get("comparison_passed") is not True:
            failures.append("manifest comparison gate is false")

        # Standalone pattern scan catches common leaked API credential forms even
        # when the original environment is unavailable to this verifier.
        credential_pattern = re.compile(rb"\b(?:sk|ak)-[A-Za-z0-9_-]{12,}\b")
        for relative in REQUIRED_ARTIFACTS:
            if credential_pattern.search((run_dir / relative).read_bytes()):
                failures.append(f"credential-shaped value found: {relative}")
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"malformed or incomplete evidence: {exc}")

    result = {"run_id": run_dir.name, "passed": not failures, "failures": failures}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
