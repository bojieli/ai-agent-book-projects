#!/usr/bin/env python3
"""Experiment 6-6: Fish Audio S1 + a 24-reference voice library."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from markup import parse
from tts import synth_direct_reference, synthesize_segments
from voice_library import DEFAULT_MANIFEST, load_voice_library

HERE = Path(__file__).parent
DEMO_TEXT = (
    "[EMO:happy][SPEED:fast][STYLE:casual]太好了！您的订单已确认。"
    "[THINKING]让我查一下发货时间。"
    "[EMO:neutral][SPEED:normal][STYLE:formal]预计明天下午送达。"
)


def strip_markers(text: str) -> str:
    return re.sub(r"\[[^]]*]|<[^>]+>", "", text).strip()


def probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)["format"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Actual Fish Audio S1 controllable TTS")
    parser.add_argument("--text", default=DEMO_TEXT)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-dir", default=str(HERE / "output"))
    parser.add_argument("--evidence", default=str(HERE / "validation" / "latest.json"))
    args = parser.parse_args()
    load_dotenv(HERE / ".env")
    if not os.getenv("FISH_API_KEY"):
        parser.error("Set FISH_API_KEY; this experiment has no substitute provider")
    library = load_voice_library(args.manifest)
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    plain = strip_markers(args.text)

    # A: no markers and no style-reference selection; direct S1 source voice.
    a = output / "A_no_control_markers.mp3"
    synth_direct_reference(plain, library["source_reference_id"], a)

    # B: one zero-shot reference clip for the complete utterance.
    b = output / "B_single_reference.mp3"
    single = [dict(type="speech", text=plain, emotion="neutral", speed="normal", style="formal", emphasis=False)]
    b_meta = synthesize_segments(single, b, output / ".tmp" / "B", manifest_path=args.manifest)

    # C: parse markers and select among the 24 real reference clips. Native
    # non-verbal markers are sent to Fish S1, rather than replaced by words.
    trace: list[str] = []
    controlled = parse(args.text, trace=trace)
    c = output / "C_24_reference_library.mp3"
    c_meta = synthesize_segments(controlled, c, output / ".tmp" / "C", manifest_path=args.manifest)

    evidence = {
        "experiment": "6-6",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "provider": "Fish Audio",
        "backend": "s1",
        "reference_profile_count": len(library["profiles"]),
        "dimensions": library["dimensions"],
        "input_with_markers": args.text,
        "parse_trace": trace,
        "outputs": {
            "A_no_control_markers": {"path": str(a), "probe": probe(a)},
            "B_single_reference": {"path": str(b), "segments": b_meta, "probe": probe(b)},
            "C_24_reference_library": {"path": str(c), "segments": c_meta, "probe": probe(c)},
        },
    }
    evidence_path = Path(args.evidence)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    for line in trace:
        print(line)
    print(f"Generated three real Fish S1 configurations; evidence: {evidence_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
