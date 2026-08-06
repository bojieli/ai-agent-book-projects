"""SOP 路径 — 由 skill pack 的 steps.yaml 驱动。"""

from __future__ import annotations

from pathlib import Path

from app.planes.pipeline.step_engine import StepEngine, StepEngineResult, StepRunState
from app.skills_runtime.skill_pack import SkillPack
from app.skills_runtime.sop_loader import load_sop_steps


def run_sop_pipeline(
    engine: StepEngine,
    meeting: StepRunState,
    skill_dir: Path,
    *,
    hitl_passed: bool = True,
    transcript_ok: bool = True,
) -> StepEngineResult:
    spec = load_sop_steps(skill_dir)
    pack = SkillPack.load(skill_dir)
    steps = list(spec["steps"])
    # 若 steps.yaml 无 artifact 步，在 extract 后插入
    if not any(s.get("type") == "artifact" for s in steps):
        insert_at = next(
            (i + 1 for i, s in enumerate(steps) if s.get("type") in {"extract", "decide"}),
            len(steps),
        )
        steps.insert(insert_at, {"id": "artifact", "type": "artifact"})
    meeting.pipeline_path = "sop"
    meeting.orchestration_mode = "sop"
    embed_step = next((s for s in steps if s.get("type") == "embed"), None)
    embed_tools = embed_step.get("tools") if embed_step else None
    return engine.run_from_spec(
        meeting,
        skill_pack=pack,
        steps=steps,
        hitl_passed=hitl_passed,
        transcript_ok=transcript_ok,
        embed_tools=embed_tools,
    )
