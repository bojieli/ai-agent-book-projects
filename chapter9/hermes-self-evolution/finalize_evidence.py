#!/usr/bin/env python3
"""Finalize and independently validate the retained Experiment 8-6 evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
RUN_ID = "exp8-6-hermes-gpt56luna-autonomous-20260802-v2"
PINNED_COMMIT = "85c8956ec7f2b4607509980794995e1c5e21e292"
SOURCE = ROOT / "worktree" / "hermes-agent"
OUTPUT = ROOT / "validation" / RUN_ID
SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9_-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
)


def command(args: list[str], *, cwd: Path = SOURCE) -> dict[str, object]:
    result = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {"command": args, "exit_code": result.returncode, "output": result.stdout}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(text: str) -> None:
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        raise RuntimeError("credential-shaped value detected in retained evidence")


def build_patch() -> str:
    patch = str(command(["git", "diff", "--binary", "--", "."])["output"])
    names = str(command(["git", "ls-files", "--others", "--exclude-standard"])["output"])
    for name in names.splitlines():
        path = SOURCE / name
        if not path.is_file():
            continue
        addition = command(
            ["git", "diff", "--no-index", "--binary", "--", "/dev/null", name]
        )
        patch += str(addition["output"])
    safe(patch)
    return patch


def main() -> int:
    if str(command(["git", "rev-parse", "HEAD"])["output"]).strip() != PINNED_COMMIT:
        raise RuntimeError("Hermes worktree is not at the pinned baseline")

    checks = [
        command(["uv", "run", "--with", "pytest", "pytest", "tests/agent/test_trajectory.py", "-q"]),
        command(
            [
                "uv", "run", "--with", "pytest", "pytest",
                "tests/test_batch_runner_checkpoint.py",
                "tests/test_batch_runner_durability.py",
                "tests/integration/test_batch_runner.py",
                "tests/test_trajectory_compressor.py", "-q",
            ]
        ),
        command(
            [
                "python3", "-m", "py_compile", "agent/trajectory.py",
                "agent/agent_runtime_helpers.py", "batch_runner.py", "run_agent.py",
                "mini_swe_runner.py", "tests/agent/test_trajectory.py",
            ]
        ),
        command(["git", "diff", "--check"]),
    ]
    if any(int(check["exit_code"]) != 0 for check in checks):
        raise RuntimeError("independent validation failed")

    patch_path = OUTPUT / "hermes-self-evolution.patch"
    patch_path.write_text(build_patch(), encoding="utf-8")
    report_path = OUTPUT / "BOOK_SELF_EVOLUTION_REPORT.md"
    shutil.copyfile(SOURCE / "BOOK_SELF_EVOLUTION_REPORT.md", report_path)

    with tempfile.TemporaryDirectory(prefix="hermes-patch-check-") as temp:
        clean = Path(temp) / "hermes-agent"
        cloned = command(["git", "clone", "--shared", str(SOURCE), str(clean)], cwd=ROOT)
        if int(cloned["exit_code"]) != 0:
            raise RuntimeError(str(cloned["output"]))
        applied = command(["git", "apply", "--check", str(patch_path)], cwd=clean)
        if int(applied["exit_code"]) != 0:
            raise RuntimeError(f"retained patch is invalid: {applied['output']}")

    transcript_names = ["hermes-transcript.txt"]
    transcript_names.extend(
        f"hermes-review-autonomous-{round_number}.txt"
        for round_number in range(1, 4)
    )
    transcript_names.extend(
        f"hermes-acceptance-review-{round_number}.txt"
        for round_number in range(1, 5)
    )
    transcript_hashes = {}
    for name in transcript_names:
        path = OUTPUT / "raw" / name
        text = path.read_text(encoding="utf-8")
        safe(text)
        transcript_hashes[name] = digest(path)
    safe(report_path.read_text(encoding="utf-8"))
    terminal_review = (OUTPUT / "raw" / "hermes-acceptance-review-4.txt").read_text(
        encoding="utf-8"
    )
    verdicts = re.findall(r"^VERDICT: (ACCEPT|REJECT)$", terminal_review, re.MULTILINE)
    if not verdicts or verdicts[-1] != "ACCEPT":
        raise RuntimeError("terminal acceptance review did not accept the candidate")

    manifest = {
        "schema_version": 2,
        "experiment": "8-6",
        "run_id": RUN_ID,
        "source_repository": "https://github.com/NousResearch/hermes-agent.git",
        "started_from_commit": PINNED_COMMIT,
        "provider": "openrouter",
        "requested_model": "openai/gpt-5.6-luna",
        "credential_environment_variable": "OPENROUTER_API_KEY",
        "candidate_gaps_supplied_in_prompt": False,
        "task_prompt_sha256": digest(ROOT / "task.md"),
        "proposer_exit_codes": [0] * 4,
        "acceptance_reviewer_exit_codes": [3, 3, 3, 0],
        "interaction_rounds": 4,
        "independent_acceptance_reviews": 4,
        "terminal_reviewer_verdict": "ACCEPT",
        "review_findings_corrected": [
            "the first parser did not understand production XML-wrapped tool responses",
            "batch and sample trajectory writers initially omitted the evaluation metadata",
            "one failed result could be double-counted",
            "the Mini-SWE trajectory writer initially remained outside the shared contract",
        ],
        "final_candidate": {
            "autonomously_selected": "evidence-backed learning signals for persisted trajectories",
            "implemented": (
                "conservative evaluation metadata shared across standard, batch, sample, "
                "and Mini-SWE trajectory persistence paths"
            ),
            "deferred": [
                "automatic mutation from a single trajectory",
                "product-level ablation campaign runner",
                "generic multi-agent reviewer without an artifact contract",
            ],
            "status": "candidate_patch_accepted_by_terminal_reviewer_not_merged",
        },
        "independent_checks": checks,
        "patch_apply_check": "passed",
        "patch_sha256": digest(patch_path),
        "report_sha256": digest(report_path),
        "transcript_sha256": transcript_hashes,
        "credential_scan": "passed",
        "claim_boundary": (
            "The run demonstrates autonomous audit, candidate generation, repeated correction under "
            "independent rejection, and terminal acceptance. It does not demonstrate downstream "
            "task-quality uplift; the proposed ablation campaign was not run."
        ),
    }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    safe(manifest_text)
    (OUTPUT / "manifest.json").write_text(manifest_text, encoding="utf-8")
    print(manifest_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
