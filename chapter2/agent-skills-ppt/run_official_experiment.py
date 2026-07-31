#!/usr/bin/env python3
"""Run Experiment 2-6 with a real skills-capable agent runtime and Anthropic's pinned PPTX Skill.

Two runtimes are supported under the author-mandated runtime-agnostic
acceptance policy (see experiment_protocol.json):

- ``--runtime claude`` (default): Claude Code, for readers with Anthropic
  credentials.
- ``--runtime kimi``: Kimi Code CLI (or an equivalent runtime), authenticated
  with KIMI_API_KEY / MOONSHOT_API_KEY.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import requests

from prepare_official_skill import prepare


ROOT = Path(__file__).resolve().parent
PROTOCOL_PATH = ROOT / "experiment_protocol.json"

CLAUDE_PROMPT = """/pptx

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

KIMI_PROMPT = """Create a polished 10–15 slide presentation from the real academic paper at
`attention-is-all-you-need.pdf` using your installed `pptx` Skill. Write the
final deck to `output/attention-is-all-you-need.pptx`.

This is an audited Agent Skills experiment. Follow the official PPTX Skill by
progressive disclosure: invoke the pptx Skill through the Skill tool (this
loads its complete SKILL.md), then read its complete html2pptx.md only after
selection. Use the pinned official `scripts/html2pptx.js` workflow. Use the
official `scripts/thumbnail.py` to make `output/full-deck-thumbnail.jpg`,
inspect the full grid, and fix visible overlap, cutoff, contrast, or alignment
defects before finishing.

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


def resolve_kimi_binary() -> str:
    binary = shutil.which("kimi")
    if binary:
        return binary
    fallback = Path.home() / ".kimi-code" / "bin" / "kimi"
    if fallback.is_file():
        return str(fallback)
    raise RuntimeError("Kimi Code CLI not found on PATH or at ~/.kimi-code/bin/kimi")


def stream_process(command: list[str], workspace: Path, env: dict, stream_path: Path,
                   stderr_path: Path, tag: str) -> int:
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
                event_type = event.get("type") or event.get("role")
                if event_type in {"assistant", "result", "system", "tool", "meta"}:
                    print(f"[{tag}] {event_type}", flush=True)
            except json.JSONDecodeError:
                pass
        return process.wait()


def run_claude(args, run_dir: Path, workspace: Path, official_skill: Path, protocol: dict) -> None:
    (workspace / ".claude" / "skills").mkdir(parents=True)
    (workspace / ".claude" / "skills" / "pptx").symlink_to(
        official_skill, target_is_directory=True
    )
    prompt = CLAUDE_PROMPT
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
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
    return_code = stream_process(
        command, workspace, env, run_dir / "claude_stream.jsonl",
        run_dir / "claude_stderr.log", "claude",
    )
    (run_dir / "claude_exit.json").write_text(
        json.dumps({"return_code": return_code}, indent=2), encoding="utf-8"
    )


def run_kimi(args, run_dir: Path, workspace: Path, official_skill: Path, protocol: dict) -> None:
    kimi = protocol["runtime"]["alternate_runtimes"]["kimi"]
    binary = resolve_kimi_binary()
    # --skills-dir replaces the auto-discovered user/project skill directories
    # for this launch, so the runtime genuinely starts with only the pinned
    # official Skill's metadata in its catalog.
    skills_dir = workspace / "kimi-skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "pptx").symlink_to(official_skill, target_is_directory=True)
    prompt = KIMI_PROMPT
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    command = [
        binary, "--prompt", prompt, "--output-format", "stream-json",
        "--model", kimi["model_alias"],
        "--skills-dir", str(skills_dir), "--add-dir", str(official_skill),
    ]
    (run_dir / "command.json").write_text(json.dumps(command, indent=2), encoding="utf-8")
    env = os.environ.copy()
    (run_dir / "runtime.json").write_text(
        json.dumps(
            {
                "runtime": "kimi",
                "binary": binary,
                "model_alias": kimi["model_alias"],
                "skills_dir": str(skills_dir),
                "auth_environment_variables_present": [
                    name for name in kimi["auth_environment_variables"] if os.getenv(name)
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return_code = stream_process(
        command, workspace, env, run_dir / "kimi_stream.jsonl",
        run_dir / "kimi_stderr.log", "kimi",
    )
    (run_dir / "kimi_exit.json").write_text(
        json.dumps({"return_code": return_code}, indent=2), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--runtime",
        choices=("claude", "kimi"),
        default="claude",
        help="Agent runtime that executes the pinned official Skill.",
    )
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
        help="Claude runtime only: use ANTHROPIC_API_KEY or explicitly use Claude Code's authenticated login.",
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
    (workspace / "output").mkdir(parents=True)
    official_skill = Path(skill_receipt["skill_path"])
    response = requests.get(protocol["paper"]["pdf_url"], timeout=180)
    response.raise_for_status()
    digest = hashlib.sha256(response.content).hexdigest()
    if digest != protocol["paper"]["pdf_sha256"]:
        raise RuntimeError(f"paper hash mismatch: {digest}")
    paper_path = workspace / "attention-is-all-you-need.pdf"
    paper_path.write_bytes(response.content)

    if args.runtime == "kimi":
        run_kimi(args, run_dir, workspace, official_skill, protocol)
    else:
        run_claude(args, run_dir, workspace, official_skill, protocol)
    validator = subprocess.run(
        [sys.executable, str(ROOT / "validate_official_run.py"), str(run_dir)]
    )
    return validator.returncode


if __name__ == "__main__":
    raise SystemExit(main())
