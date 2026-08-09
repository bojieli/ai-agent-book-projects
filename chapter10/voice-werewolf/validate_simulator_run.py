#!/usr/bin/env python3
"""Independently recompute the simulated-user audio/action boundary from a report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from werewolf.human import HumanPlayerAgent


def validate(report_path: Path) -> dict:
    raw = report_path.read_bytes()
    report = json.loads(raw)
    events = report.get("voice_events", [])
    errors = []
    checked = 0
    seen_sequences = set()
    seen_request_ids = set()
    seen_provider_ids = set()
    simulator_asr_count = sum(
        isinstance(event, dict) and event.get("type") == "simulator_asr"
        for event in events
    ) if isinstance(events, list) else 0
    simulator_tool_count = 0

    if not isinstance(events, list):
        errors.append("voice_events must be an array")
        events = []

    # A trace is an append-only sequence.  Reject duplicate/out-of-order sequence
    # numbers instead of allowing a later event to be accidentally paired with an
    # earlier action.
    previous_sequence = 0
    for event in events:
        if not isinstance(event, dict):
            errors.append("every voice event must be an object")
            continue
        sequence = event.get("sequence")
        if isinstance(sequence, int) and sequence in seen_sequences:
            errors.append(f"duplicate voice event sequence: {sequence}")
        if not isinstance(sequence, int) or sequence <= previous_sequence:
            errors.append(f"voice event sequence is not strictly increasing: {sequence!r}")
        if isinstance(sequence, int):
            seen_sequences.add(sequence)
            previous_sequence = max(previous_sequence, sequence)

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        if event.get("type") != "simulator_llm_tool":
            continue
        checked += 1
        simulator_tool_count += 1
        tool_request_id = event.get("response_id") or event.get("request_id")
        if not isinstance(tool_request_id, str) or not tool_request_id.strip():
            errors.append(f"tool event {event.get('sequence')} lacks provider response_id")
        elif tool_request_id in seen_provider_ids:
            errors.append(f"duplicate tool provider response_id: {tool_request_id}")
        else:
            seen_provider_ids.add(tool_request_id)
        seat = event.get("seat")
        if not isinstance(seat, str) or not re.fullmatch(r"P\d+", seat):
            errors.append(f"tool event {event.get('sequence')} has invalid seat")
        # Only events in this action's contiguous transaction may be used.  The
        # old validator searched to the end of the trace, so a missing ASR could
        # silently borrow another turn's transcript.
        transaction = []
        for item in events[index + 1:]:
            if not isinstance(item, dict):
                errors.append(f"tool event {event.get('sequence')} has non-object transaction event")
                continue
            if item.get("type") == "simulator_llm_tool":
                break
            transaction.append(item)
        tts = next((item for item in transaction
                    if item.get("type") == "tts_ready" and item.get("speaker") == seat), None)
        following = next((item for item in transaction
                          if item.get("type") == "simulator_asr"), None)
        if tts is None:
            errors.append(f"tool event {event.get('sequence')} has no same-seat TTS")
        if following is None:
            errors.append(f"tool event {event.get('sequence')} has no transaction-local simulator_asr")
            continue
        if tts is not None:
            if transaction.index(tts) > transaction.index(following):
                errors.append(f"tool event {event.get('sequence')} has ASR before TTS")
            audio_hash = tts.get("audio_sha256")
            source_hash = following.get("source_audio_sha256")
            if not isinstance(audio_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", audio_hash):
                errors.append(f"tool event {event.get('sequence')} has invalid TTS audio hash")
            if source_hash != audio_hash:
                errors.append(f"tool event {event.get('sequence')} ASR source hash does not match TTS")
            if not isinstance(tts.get("audio_bytes"), int) or tts["audio_bytes"] <= 0:
                errors.append(f"tool event {event.get('sequence')} has empty TTS audio")
        request_id = following.get("request_id")
        if not isinstance(request_id, str) or not request_id.strip():
            errors.append(f"ASR event for tool {event.get('sequence')} lacks request_id")
        elif request_id in seen_request_ids:
            errors.append(f"duplicate ASR request_id: {request_id}")
        else:
            seen_request_ids.add(request_id)
            if request_id in seen_provider_ids:
                errors.append(f"provider response_id reused by ASR: {request_id}")
            seen_provider_ids.add(request_id)
        arguments = event.get("arguments") or {}
        if event.get("tool") == "speak_publicly":
            if not str(following.get("transcript", "")).strip():
                errors.append(f"speech tool event {event.get('sequence')} has empty ASR")
            continue
        target = arguments.get("target")
        transcript = str(following.get("transcript", ""))
        if target == "none":
            if not HumanPlayerAgent._explicit_none(transcript):
                errors.append(
                    f"tool event {event.get('sequence')} selected none but ASR was not an "
                    f"explicit abstention: {transcript!r}"
                )
        elif target and target not in transcript.replace(" ", ""):
            # English word-number transcripts are valid too; use the production parser
            # with the report roster as candidates.
            try:
                player_count = int(report["players"])
            except (KeyError, TypeError, ValueError):
                player_count = 0
                errors.append("report players must be an integer")
            candidates = [f"P{number}" for number in range(1, player_count + 1)]
            parsed = HumanPlayerAgent._spoken_target(transcript, candidates, False)
            if parsed != target:
                errors.append(
                    f"tool event {event.get('sequence')} selected {target} but ASR parsed {parsed}"
                )
    if simulator_tool_count != report.get("simulator_llm_tool_calls", simulator_tool_count):
        errors.append("report simulator_llm_tool_calls does not match trace")
    if simulator_asr_count != report.get("simulator_audio_roundtrips", simulator_asr_count):
        errors.append("report simulator_audio_roundtrips does not match trace")
    if any(isinstance(event, dict) and event.get("type") == "simulator_action_mismatch"
           for event in events):
        errors.append("trace contains simulator_action_mismatch")
    return {
        "schema_version": 1,
        "source_report": str(report_path),
        "source_report_sha256": hashlib.sha256(raw).hexdigest(),
        "simulator_tool_events_checked": checked,
        "strict_audio_action_boundary": "pass" if checked and not errors else "fail",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.report)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["strict_audio_action_boundary"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
