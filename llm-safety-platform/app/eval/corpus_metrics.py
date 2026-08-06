"""Compute corpus scale metrics from YAML files (fail-closed SoT)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "configs" / "evals" / "attack_corpora"
EXPANDED_DIR = CORPUS / "handbook_expanded"

Profile = Literal["ci", "release", "full"]


def _count_cases(path: Path, *, expect: str | None = None, limit: int | None = None) -> int:
    from app.redteam.corpus_runner import load_cases

    if not path.exists():
        return 0
    cases = load_cases(path, limit)
    if expect is None:
        return len(cases)
    return len([c for c in cases if c.get("expect", "block") == expect])


def _expanded_block_count(limit: int | None) -> tuple[int, int]:
    """Return (block_case_count, scenario_file_count excluding benign_controls)."""
    block = 0
    files = 0
    for f in sorted(EXPANDED_DIR.glob("*.yaml")):
        if f.name == "benign_controls.yaml":
            continue
        files += 1
        block += _count_cases(f, expect="block", limit=limit)
    return block, files


@lru_cache(maxsize=1)
def compute_corpus_metrics(expanded_limit: int = 20) -> dict[str, Any]:
    """Derive profile case counts from on-disk corpora."""
    smoke_block = _count_cases(CORPUS / "handbook_expanded_smoke.yaml", expect="block")
    benign_fp = _count_cases(CORPUS / "benign_fp_suite.yaml", expect="allow")
    benign_controls = _count_cases(CORPUS / "handbook_expanded/benign_controls.yaml", expect="allow")
    expanded_block_full, scenario_files = _expanded_block_count(None)
    expanded_block_sample, _ = _expanded_block_count(expanded_limit)

    profiles = {
        "ci": {"attack": smoke_block, "fp": benign_fp},
        "release": {"attack": smoke_block + expanded_block_sample, "fp": benign_fp + benign_controls},
        "full": {"attack": expanded_block_full, "fp": benign_fp + benign_controls},
    }

    return {
        "total_corpus": expanded_block_full + benign_controls,
        "expect_block": expanded_block_full,
        "benign_controls_allow": benign_controls,
        "benign_fp_allow": benign_fp,
        "expanded_scenarios": scenario_files,
        "expanded_limit": expanded_limit,
        "profiles": profiles,
        "sources": {
            "smoke_block": str(CORPUS / "handbook_expanded_smoke.yaml"),
            "benign_fp": str(CORPUS / "benign_fp_suite.yaml"),
            "benign_controls": str(CORPUS / "handbook_expanded/benign_controls.yaml"),
            "expanded_dir": str(EXPANDED_DIR),
        },
    }


def assert_profile_metrics(profile: Profile, *, attack: int, fp: int, expanded_limit: int = 20) -> None:
    """Fail-closed if on-disk corpora drift from expected profile sizes."""
    m = compute_corpus_metrics(expanded_limit)
    prof = m["profiles"][profile]
    if prof["attack"] != attack or prof["fp"] != fp:
        raise AssertionError(
            f"corpus metrics drift for {profile}: expected attack={attack} fp={fp}, "
            f"computed attack={prof['attack']} fp={prof['fp']}"
        )


def get_corpus_metrics(expanded_limit: int = 20) -> dict[str, Any]:
    return compute_corpus_metrics(expanded_limit)
