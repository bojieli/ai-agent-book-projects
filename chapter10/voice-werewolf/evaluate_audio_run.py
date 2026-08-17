#!/usr/bin/env python3
"""Direct-audio independent evaluation of simulator utterances through OpenRouter."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from openai import OpenAI


WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
    6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_text(tool_event: dict[str, Any]) -> str:
    arguments = tool_event.get("arguments") or {}
    if tool_event.get("tool") == "speak_publicly":
        return str(arguments.get("utterance", "")).strip()
    target = str(arguments.get("target", "")).strip()
    if target == "none":
        return "I choose to abstain."
    number = int(target.removeprefix("P"))
    return f"I choose player {WORDS.get(number, str(number))}."


def parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    return json.loads(text)


def evaluate(report_path: Path, output: Path, model: str) -> dict[str, Any]:
    if not os.getenv("OPENROUTER_API_KEY"):
        raise RuntimeError("OPENROUTER_API_KEY is required")
    raw = report_path.read_bytes()
    report = json.loads(raw)
    events = report.get("voice_events") or []
    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        timeout=120,
        max_retries=2,
    )
    rows = []
    for index, event in enumerate(events):
        if event.get("type") != "simulator_llm_tool":
            continue
        seat = event.get("seat")
        # Treat each tool -> TTS -> ASR sequence as a transaction.  Searching to
        # the end of the report can pair a failed turn with a later player's audio
        # and produce a false positive independent evaluation.
        transaction = []
        for item in events[index + 1:]:
            if item.get("type") == "simulator_llm_tool":
                break
            transaction.append(item)
        tts = next(
            (item for item in transaction
             if item.get("type") == "tts_ready" and item.get("speaker") == seat),
            None,
        )
        asr = next(
            (item for item in transaction if item.get("type") == "simulator_asr"),
            None,
        )
        if not tts or not asr:
            raise ValueError(f"tool event {event.get('sequence')} lacks TTS/ASR evidence")
        if transaction.index(tts) > transaction.index(asr):
            raise ValueError(f"tool event {event.get('sequence')} has ASR before TTS")
        if asr.get("source_audio_sha256") != tts.get("audio_sha256"):
            raise ValueError(f"tool event {event.get('sequence')} ASR/TTS audio hash mismatch")
        audio_path = Path(str(tts["file"]))
        if not audio_path.is_absolute():
            project_root = next(
                parent for parent in report_path.resolve().parents
                if parent.name == "voice-werewolf"
            )
            candidates = [Path.cwd() / audio_path, project_root / audio_path]
            audio_path = next((path for path in candidates if path.is_file()), candidates[0])
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        if sha256(audio_path) != tts.get("audio_sha256"):
            raise ValueError(f"audio hash mismatch: {audio_path}")
        expected = expected_text(event)
        started = time.perf_counter()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Independently evaluate this synthetic Werewolf-game speech audio. "
                                f"The intended text is: {expected!r}. Return one JSON object only with "
                                "keys transcript (string), intelligibility_1_to_5 (integer), "
                                "semantic_fidelity_1_to_5 (integer), naturalness_1_to_5 (integer), "
                                "action_or_seat_preserved (boolean), and rationale (short string). "
                                "Judge the waveform itself. A robotic voice may score low on naturalness "
                                "without losing intelligibility or semantic fidelity."
                            ),
                        },
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": base64.b64encode(audio_path.read_bytes()).decode("ascii"),
                                "format": audio_path.suffix.lstrip(".").lower(),
                            },
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=600,
        )
        judgment = parse_json(response.choices[0].message.content or "")
        usage = response.usage.model_dump() if response.usage else None
        row = {
            "tool_sequence": event.get("sequence"),
            "tts_sequence": tts.get("sequence"),
            "asr_sequence": asr.get("sequence"),
            "tool": event.get("tool"),
            "target": (event.get("arguments") or {}).get("target"),
            "expected_text": expected,
            "original_asr_transcript": asr.get("transcript"),
            "audio_file": str(audio_path.relative_to(Path.cwd())),
            "audio_bytes": audio_path.stat().st_size,
            "audio_sha256": sha256(audio_path),
            "judge": judgment,
            "request_id": response.id,
            "provider_reported_model": response.model,
            "usage": usage,
            "latency_seconds": round(time.perf_counter() - started, 3),
        }
        row["pass"] = bool(
            int(judgment.get("intelligibility_1_to_5", 0)) >= 4
            and int(judgment.get("semantic_fidelity_1_to_5", 0)) >= 4
            and judgment.get("action_or_seat_preserved") is True
        )
        rows.append(row)

    result = {
        "schema_version": 1,
        "experiment": "10-6-independent-audio-evaluation",
        "source_report": str(report_path),
        "source_report_sha256": hashlib.sha256(raw).hexdigest(),
        "provider": "OpenRouter multimodal audio API",
        "requested_model": model,
        "evaluations": rows,
        "gates": {
            "all_simulator_audio_evaluated": len(rows)
            == sum(event.get("type") == "simulator_llm_tool" for event in events),
            "unique_real_request_ids": len({row["request_id"] for row in rows}) == len(rows),
            "all_audio_hashes_match": bool(rows),
            "all_intelligible_and_semantically_faithful": bool(rows)
            and all(row["pass"] for row in rows),
        },
    }
    result["status"] = "pass" if all(result["gates"].values()) else "fail"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="google/gemini-3-flash-preview")
    args = parser.parse_args()
    result = evaluate(args.report, args.output, args.model)
    print(json.dumps({"status": result["status"], "gates": result["gates"]}, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
