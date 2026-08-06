"""Playbook 路径 — Default Playbook + 场景 overrides。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.planes.pipeline.step_engine import StepEngine, StepEngineResult, StepRunState
from app.skills_runtime.skill_pack import SkillPack
from app.skills_runtime.sop_loader import assert_no_sop_for_playbook


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_playbook_steps(repo_root: Path, skill_dir: Path) -> list[dict[str, Any]]:
    """合并 default playbook 与场景 playbook_overrides.yaml。"""
    assert_no_sop_for_playbook(skill_dir)
    base = _load_yaml(repo_root / "app" / "playbooks" / "default.yaml")
    steps = list(base.get("steps") or [])
    override_path = skill_dir / "playbook_overrides.yaml"
    if override_path.exists():
        ov = _load_yaml(override_path)
        patches = {p["id"]: p for p in ov.get("steps_patch") or []}
        merged: list[dict[str, Any]] = []
        for step in steps:
            sid = step["id"]
            if sid in patches:
                patched = {**step, **patches[sid]}
                merged.append(patched)
            else:
                merged.append(step)
        steps = merged
    return steps


def run_playbook_pipeline(
    engine: StepEngine,
    meeting: StepRunState,
    skill_dir: Path,
    repo_root: Path,
    *,
    hitl_passed: bool = True,
    transcript_ok: bool = True,
) -> StepEngineResult:
    pack = SkillPack.load(skill_dir)
    steps = load_playbook_steps(repo_root, skill_dir)
    meeting.pipeline_path = "playbook"
    meeting.orchestration_mode = "playbook"
    return engine.run_from_spec(
        meeting,
        skill_pack=pack,
        steps=steps,
        hitl_passed=hitl_passed,
        transcript_ok=transcript_ok,
    )


def run_safe_fallback(
    engine: StepEngine,
    meeting: StepRunState,
    skill_dir: Path,
    *,
    hitl_passed: bool = True,
) -> StepEngineResult:
    """未知场景 L0 安全降级：只读纪要，不 embed、不写 Continuum。"""
    pack = SkillPack.load(skill_dir)
    steps = [
        {"id": "understand", "type": "understand"},
        {"id": "artifact", "type": "artifact"},
        {"id": "schema_validate", "type": "validate", "hook": "schema_validate", "wall": True},
        {"id": "policy_hooks", "type": "validate", "hook": "policy_hooks", "wall": True},
        {"id": "evaluate", "type": "evaluate", "wall": True},
        {"id": "hitl", "type": "hitl"},
        {"id": "embed", "type": "embed", "skip_if": "maturity == L0"},
        {"id": "continuum_index", "type": "index"},
        {"id": "render", "type": "render"},
    ]
    meeting.pipeline_path = "fallback"
    meeting.orchestration_mode = "playbook"
    meeting.maturity = "L0"
    return engine.run_from_spec(
        meeting,
        skill_pack=pack,
        steps=steps,
        hitl_passed=hitl_passed,
        transcript_ok=True,
    )
