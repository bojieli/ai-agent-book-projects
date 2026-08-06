"""Validate all V1 Skill Packs exist and match orchestration_mode rules."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "app" / "skills"

V1 = {
    "R1": ("eng/R1_req_sync", "playbook"),
    "R4": ("eng/R4_release_review", "sop"),
    "R5": ("eng/R5_delivery_sync", "playbook"),
    "B4": ("business/B4_business_review", "playbook"),
    "B5": ("business/B5_limit_pricing", "sop"),
    "H2": ("hr/H2_perf_calibration", "playbook"),
    "H5": ("hr/H5_org_change", "playbook"),
    "K1": ("risk/K1_policy_review", "sop"),
    "K5": ("risk/K5_model_monitor", "sop"),
    "C2": ("compliance/C2_remediation", "sop"),
    "X1": ("cross/X1_gray_ambiguity", "playbook"),
    "general": ("platform/general", "playbook"),
}


def _front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def main() -> int:
    failures: list[str] = []
    for story, (rel, mode) in V1.items():
        base = SKILLS / rel
        skill = base / "SKILL.md"
        if not skill.exists():
            failures.append(f"{story}: missing {skill}")
            continue
        meta = _front_matter(skill.read_text(encoding="utf-8"))
        if meta.get("orchestration_mode") != mode:
            failures.append(
                f"{story}: mode want={mode} got={meta.get('orchestration_mode')}"
            )
        sop = base / "sop" / "steps.yaml"
        if mode == "sop" and not sop.exists():
            failures.append(f"{story}: sop mode missing steps.yaml")
        if mode == "playbook" and sop.exists():
            failures.append(f"{story}: playbook must not invent sop/steps.yaml")
        schemas = list((base / "schemas").glob("*.json")) if (base / "schemas").exists() else []
        if not schemas:
            failures.append(f"{story}: missing schemas/")
        if not (base / "eval").exists():
            failures.append(f"{story}: missing eval/")
        # critical sealed
        if meta.get("classification") == "critical":
            if meta.get("continuum_write_class") not in {"sealed", "none"}:
                failures.append(f"{story}: critical write_class invalid")
            if meta.get("default_embed_gate") != "block":
                failures.append(f"{story}: critical embed_gate must block")

    if failures:
        print("SKILL SMOKE FAILED:")
        for f in failures:
            print(" -", f)
        return 1
    print(f"SKILL SMOKE PASSED ({len(V1)} packs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
