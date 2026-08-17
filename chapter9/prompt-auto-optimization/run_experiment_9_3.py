#!/usr/bin/env python3
"""Run the full Experiment 9-3 campaign and save canonical evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from airline_env import CASES
from demo import main as run_campaign


ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("openrouter", "moonshot", "ark", "openai"), default="openrouter")
    parser.add_argument("--model", default="openai/gpt-4o-mini")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    os.environ["LLM_PROVIDER"] = args.provider
    os.environ["LLM_MODEL"] = args.model
    stamp = datetime.now(timezone.utc).strftime("real_%Y%m%dT%H%M%SZ")
    output_dir = args.output_dir or ROOT / "validation" / stamp
    output_dir.mkdir(parents=True, exist_ok=False)
    evidence_path = output_dir / "evidence.json"
    summary = run_campaign(cases=CASES, rounds=args.rounds, output=str(evidence_path))
    payload = evidence_path.read_text(encoding="utf-8")
    (ROOT / "validation").mkdir(exist_ok=True)
    (ROOT / "validation" / "latest.json").write_text(payload, encoding="utf-8")
    print(json.dumps({
        "evidence": str(evidence_path.relative_to(ROOT)),
        "sha256": hashlib.sha256(payload.encode()).hexdigest(),
        "execution_accepted": summary["acceptance"]["execution_accepted"],
        "all_manuscript_result_claims_observed": summary["acceptance"]["all_manuscript_result_claims_observed"],
        "release_decision": summary["release_gate"]["decision"],
        "usage": summary["usage"],
    }, ensure_ascii=False, indent=2))
    return 0 if summary["acceptance"]["execution_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
