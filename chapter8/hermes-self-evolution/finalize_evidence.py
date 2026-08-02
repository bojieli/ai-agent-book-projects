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
RUN_ID = "exp8-6-hermes-gpt56luna-20260802-v1"
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
        command(["uv", "run", "--with", "pytest", "pytest", "tests/agent/test_model_status_context.py", "-q"]),
        command(
            [
                "uv", "run", "--with", "pytest", "pytest",
                "tests/agent/test_api_content_sidecar.py",
                "tests/run_agent/test_background_review_cache_parity.py",
                "tests/agent/test_turn_context.py", "-q",
            ]
        ),
        command(
            [
                "python3", "-m", "py_compile", "agent/model_status_context.py",
                "agent/conversation_loop.py", "agent/agent_init.py", "run_agent.py",
                "hermes_state.py",
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
        "hermes-review-transcript.txt" if round_number == 1
        else f"hermes-review-{round_number}-transcript.txt"
        for round_number in range(1, 9)
    )
    transcript_names.extend(
        f"hermes-acceptance-review-{round_number}.txt"
        for round_number in range(1, 7)
    )
    transcript_hashes = {}
    for name in transcript_names:
        path = OUTPUT / "raw" / name
        text = path.read_text(encoding="utf-8")
        safe(text)
        transcript_hashes[name] = digest(path)
    safe(report_path.read_text(encoding="utf-8"))
    terminal_review = (OUTPUT / "raw" / "hermes-acceptance-review-6.txt").read_text(
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
        "proposer_exit_codes": [0] * 9,
        "acceptance_reviewer_exit_codes": [3, 3, 3, 3, 3, 0],
        "interaction_rounds": 9,
        "independent_acceptance_reviews": 6,
        "terminal_reviewer_verdict": "ACCEPT",
        "review_findings_corrected": [
            "request-local status rewrote prior wire bytes",
            "test replay accepted sidecar types that production rejected",
            "list sidecars did not survive the string-only persistence boundary",
            "tool-result attachment was not durably replayed and todo identifiers were unbounded",
            "status disappeared or preceded evidence in realistic assistant-tool-call sequences",
            "post-flush sidecars were not backfilled to persisted rows",
            "same-message retries appended duplicate status projections",
            "pre-existing memory and plugin sidecars suppressed status projection",
        ],
        "final_candidate": {
            "implemented": "opt-in model-visible status projection for string-content turns",
            "deferred": [
                "product-level ablation runner",
                "general persistent-memory forgetting",
                "universal proposer-reviewer artifact contract",
                "multimodal status injection",
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
