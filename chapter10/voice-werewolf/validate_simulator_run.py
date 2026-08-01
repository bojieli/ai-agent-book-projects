#!/usr/bin/env python3
"""Independently recompute the simulated-user audio/action boundary from a report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from werewolf.human import HumanPlayerAgent


def validate(report_path: Path) -> dict:
    raw = report_path.read_bytes()
    report = json.loads(raw)
    events = report.get("voice_events", [])
    errors = []
    checked = 0
    for index, event in enumerate(events):
        if event.get("type") != "simulator_llm_tool":
            continue
        checked += 1
        following = next(
            (item for item in events[index + 1:] if item.get("type") == "simulator_asr"),
            None,
        )
        if following is None:
            errors.append(f"tool event {event.get('sequence')} has no later simulator_asr")
            continue
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
            candidates = [f"P{number}" for number in range(1, report["players"] + 1)]
            parsed = HumanPlayerAgent._spoken_target(transcript, candidates, False)
            if parsed != target:
                errors.append(
                    f"tool event {event.get('sequence')} selected {target} but ASR parsed {parsed}"
                )
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
