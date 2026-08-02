#!/usr/bin/env python3
"""Clone a pinned Hermes snapshot and let Hermes audit/update its own code.

The runner keeps credentials outside retained evidence. Normal working state is
written beneath ignored ``worktree/`` and ``.hermes-home/`` directories; the
curated manifest and patch are written to ``validation/<run-id>/``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent
REPO_URL = "https://github.com/NousResearch/hermes-agent.git"
PINNED_COMMIT = "85c8956ec7f2b4607509980794995e1c5e21e292"
DEFAULT_MODEL = "openai/gpt-5.6-luna"
SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
)


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_no_secrets(text: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise RuntimeError("credential-shaped value detected in retained evidence")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--model", default=os.getenv("HERMES_EXPERIMENT_MODEL", DEFAULT_MODEL))
    parser.add_argument("--provider", default="openrouter")
    parser.add_argument("--reuse-worktree", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not os.getenv("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is required for the live run", file=sys.stderr)
        return 2

    run_id = args.run_id or datetime.now(timezone.utc).strftime("exp8-6-hermes-%Y%m%dT%H%M%SZ")
    source = ROOT / "worktree" / "hermes-agent"
    hermes_home = ROOT / ".hermes-home" / run_id
    output = ROOT / "validation" / run_id
    raw = output / "raw"
    output.mkdir(parents=True, exist_ok=False)
    raw.mkdir()

    if source.exists() and not args.reuse_worktree:
        shutil.rmtree(source)
    if not source.exists():
        source.parent.mkdir(parents=True, exist_ok=True)
        cloned = run(["git", "clone", "--no-tags", REPO_URL, str(source)])
        if cloned.returncode:
            print(cloned.stdout, file=sys.stderr)
            return cloned.returncode

    checkout = run(["git", "checkout", "--detach", PINNED_COMMIT], cwd=source)
    if checkout.returncode:
        print(checkout.stdout, file=sys.stderr)
        return checkout.returncode

    baseline = run(["git", "rev-parse", "HEAD"], cwd=source).stdout.strip()
    if baseline != PINNED_COMMIT:
        raise RuntimeError(f"wrong baseline: {baseline}")

    if not args.skip_install:
        installed = run(["uv", "sync", "--python", "3.12"], cwd=source, capture=False)
        if installed.returncode:
            return installed.returncode

    env = os.environ.copy()
    env.update(
        {
            "HERMES_HOME": str(hermes_home),
            "HERMES_YOLO_MODE": "1",
            "PYTHONUNBUFFERED": "1",
        }
    )
    prompt = (ROOT / "task.md").read_text(encoding="utf-8")
    command = [
        "uv",
        "run",
        "hermes",
        "chat",
        "--provider",
        args.provider,
        "--model",
        args.model,
        "--toolsets",
        "terminal,skills",
        "-q",
        prompt,
    ]
    agent_run = run(command, cwd=source, env=env)
    transcript = agent_run.stdout or ""
    assert_no_secrets(transcript)
    (raw / "hermes-transcript.txt").write_text(transcript, encoding="utf-8")

    diff = run(["git", "diff", "--binary", "--", "."], cwd=source).stdout
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], cwd=source).stdout.splitlines()
    for name in untracked:
        path = source / name
        if path.is_file():
            # Keep paths relative to ``source``. Absolute paths produce invalid
            # ``diff --git ab/... bb/...`` headers after naive replacement.
            addition = run(
                ["git", "diff", "--no-index", "--binary", "--", "/dev/null", name],
                cwd=source,
            ).stdout
            diff += addition
    assert_no_secrets(diff)
    patch_path = output / "hermes-self-evolution.patch"
    patch_path.write_text(diff, encoding="utf-8")

    report_source = source / "BOOK_SELF_EVOLUTION_REPORT.md"
    if report_source.exists():
        report_text = report_source.read_text(encoding="utf-8")
        assert_no_secrets(report_text)
        (output / "BOOK_SELF_EVOLUTION_REPORT.md").write_text(report_text, encoding="utf-8")

    status = run(["git", "status", "--short"], cwd=source).stdout
    manifest = {
        "schema_version": 1,
        "experiment": "8-6",
        "run_id": run_id,
        "started_from_commit": baseline,
        "source_repository": REPO_URL,
        "provider": args.provider,
        "requested_model": args.model,
        "credential_environment_variable": "OPENROUTER_API_KEY",
        "agent_exit_code": agent_run.returncode,
        "git_status": status.splitlines(),
        "transcript_sha256": sha256(raw / "hermes-transcript.txt"),
        "patch_sha256": sha256(patch_path),
        "report_present": report_source.exists(),
        "claim_boundary": (
            "A completed coding run demonstrates autonomous auditing and patch generation; "
            "it does not establish downstream task-quality uplift without the proposed ablation campaign."
        ),
    }
    manifest_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    assert_no_secrets(manifest_text)
    (output / "manifest.json").write_text(manifest_text, encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return agent_run.returncode


if __name__ == "__main__":
    raise SystemExit(main())
