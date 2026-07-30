#!/usr/bin/env python3
"""Evaluate real Step-Audio R1 on Spoken-MQA/URO-style audio and a cascade."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from speech_model import CascadeClient, StepAudioR1Client

HERE = Path(__file__).parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Experiment 9-4: exact Step-Audio R1 evaluation")
    parser.add_argument("--endpoint", default=os.getenv("STEP_AUDIO_ENDPOINT", "http://localhost:9999"))
    parser.add_argument("--audio", action="append", required=True)
    parser.add_argument("--task", action="append", choices=["spoken-mqa", "uro-bench"], required=True)
    parser.add_argument("--instruction", action="append", required=True)
    parser.add_argument("--skip-cascade", action="store_true")
    parser.add_argument("--evidence", default=str(HERE / "validation" / "latest.json"))
    args = parser.parse_args()
    if not (len(args.audio) == len(args.task) == len(args.instruction)):
        parser.error("--audio, --task and --instruction counts must match")
    load_dotenv(HERE / ".env")
    step = StepAudioR1Client(args.endpoint)
    health = step.healthcheck()  # fail early: evidence may never call a substitute
    cascade = None
    if not args.skip_cascade:
        if not os.getenv("OPENAI_API_KEY"):
            parser.error("Cascade baseline needs OPENAI_API_KEY (or pass --skip-cascade)")
        cascade = CascadeClient(OpenAI(timeout=180, max_retries=3))
    cases = []
    for audio, task, instruction in zip(args.audio, args.task, args.instruction):
        direct = step.infer(audio, instruction)
        control = cascade.infer(audio, instruction) if cascade else None
        print(f"[{task}] Step-Audio R1 ({direct.first_token_seconds:.3f}s TTFT): {direct.response}")
        if control:
            print(f"[{task}] Cascade ({control.latency_seconds:.3f}s): {control.response}")
        cases.append({
            "task": task,
            "audio": audio,
            "instruction": instruction,
            "step_audio_r1": direct.to_dict(),
            "cascade": control.to_dict() if control else None,
        })
    evidence = {
        "experiment": "9-4",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "endpoint": args.endpoint,
        "served_models": health.get("data", []),
        "cases": cases,
    }
    output = Path(args.evidence)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Sanitized evidence: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
