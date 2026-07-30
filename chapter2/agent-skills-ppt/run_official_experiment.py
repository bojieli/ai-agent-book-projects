#!/usr/bin/env python3
"""Run Experiment 2-6 with real Claude Code and Anthropic's pinned PPTX Skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import requests

from prepare_official_skill import prepare


ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = ROOT / "experiment_protocol.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--official-repo",
        type=Path,
        default=ROOT / "external" / "anthropics-skills",
    )
    parser.add_argument("--resume-validation", action="store_true")
    parser.add_argument(
        "--auth-source",
        choices=("environment", "claude-login"),
        default="environment",
        help="Use ANTHROPIC_API_KEY or explicitly use Claude Code's authenticated login.",
    )
    args = parser.parse_args()
    run_dir = args.output.resolve()
    if args.resume_validation:
        return subprocess.run(
            [sys.executable, str(ROOT / "validate_official_run.py"), str(run_dir)]
        ).returncode
    run_dir.mkdir(parents=True, exist_ok=False)
    protocol_bytes = PROTOCOL_PATH.read_bytes()
    protocol = json.loads(protocol_bytes)
    (run_dir / "experiment_protocol.json").write_bytes(protocol_bytes)
    skill_receipt = prepare(args.official_repo)
    (run_dir / "official_skill_receipt.json").write_text(
        json.dumps(skill_receipt, indent=2), encoding="utf-8"
    )

    workspace = run_dir / "workspace"
    (workspace / ".claude" / "skills").mkdir(parents=True)
    (workspace / "output").mkdir(parents=True)
    official_skill = Path(skill_receipt["skill_path"])
    (workspace / ".claude" / "skills" / "pptx").symlink_to(
        official_skill, target_is_directory=True
    )
    response = requests.get(protocol["paper"]["pdf_url"], timeout=180)
    response.raise_for_status()
    digest = hashlib.sha256(response.content).hexdigest()
    if digest != protocol["paper"]["pdf_sha256"]:
        raise RuntimeError(f"paper hash mismatch: {digest}")
    paper_path = workspace / "attention-is-all-you-need.pdf"
    paper_path.write_bytes(response.content)

    prompt = """/pptx

Create a polished 10–15 slide presentation from the real academic paper at
`attention-is-all-you-need.pdf`. Write the final deck to
`output/attention-is-all-you-need.pptx`.

This is an audited Agent Skills experiment. Follow the official PPTX Skill by
progressive disclosure: invoke the pptx Skill, read its complete SKILL.md, then
read its complete html2pptx.md only after selection. Use the pinned official
`scripts/html2pptx.js` workflow. Use the official `scripts/thumbnail.py` to
make `output/full-deck-thumbnail.jpg`, inspect the full grid, and fix visible
overlap, cutoff, contrast, or alignment defects before finishing.

Content gates:
- cover title, problem/background, Transformer method/architecture, key
  experimental results, and conclusion;
- extract or crop at least three visuals directly from the source PDF (not
  invented replacements), place the files under `source_visuals/`, and embed
  all of them in the deck;
- create `source_visuals/manifest.json` as a JSON list. Each item must contain
  `file`, one-based PDF `page`, the paper's `label` (for example Figure 1 or
  Table 2), and a faithful `caption`;
- make every visual consistent with the surrounding slide explanation and
  cite its source page/label on-slide.

You may install the Node packages required by the official Skill inside this
workspace. Do not use the repository's bundled `demo.py`, local proxy Skill,
or prewritten sample outline. The final response must name the deck,
thumbnail, visual manifest, slide count, validation performed, and any
remaining limitation.
"""
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    stream_path = run_dir / "claude_stream.jsonl"
    stderr_path = run_dir / "claude_stderr.log"
    command = [
        # Put the positional prompt before --add-dir.  The current Claude Code
        # CLI declares --add-dir as variadic, so a trailing prompt is otherwise
        # consumed as another directory and --print reports that no input was
        # provided.
        "claude", prompt, "--print", "--output-format", "stream-json", "--verbose",
        "--model", protocol["runtime"]["model_alias"], "--effort", "high",
        "--max-budget-usd", "8", "--no-session-persistence",
        "--dangerously-skip-permissions", "--add-dir", str(official_skill),
    ]
    (run_dir / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
    env = os.environ.copy()
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    if args.auth_source == "claude-login":
        # An invalid environment key takes precedence over an otherwise valid
        # Claude Code OAuth login.  Make this explicit and record it without
        # ever serializing credential values.
        env.pop("ANTHROPIC_API_KEY", None)
    (run_dir / "auth_source.json").write_text(
        json.dumps({"auth_source": args.auth_source}, indent=2), encoding="utf-8"
    )
    with stream_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_file:
        process = subprocess.Popen(
            command,
            cwd=workspace,
            env=env,
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            stdout_file.write(line)
            stdout_file.flush()
            try:
                event = json.loads(line)
                event_type = event.get("type")
                if event_type in {"assistant", "result", "system"}:
                    print(f"[claude] {event_type}", flush=True)
            except json.JSONDecodeError:
                pass
        return_code = process.wait()
    (run_dir / "claude_exit.json").write_text(
        json.dumps({"return_code": return_code}, indent=2), encoding="utf-8"
    )
    validator = subprocess.run(
        [sys.executable, str(ROOT / "validate_official_run.py"), str(run_dir)]
    )
    return validator.returncode


if __name__ == "__main__":
    raise SystemExit(main())
