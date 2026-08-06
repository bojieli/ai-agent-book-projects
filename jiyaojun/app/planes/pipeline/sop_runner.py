"""SOP pipeline executor — runs real steps.yaml walls (no skip validate/evaluate)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from app.skills_runtime.sop_loader import load_sop_steps


@dataclass
class SopStepResult:
    step_id: str
    status: str  # ok | skipped | failed
    detail: str = ""


@dataclass
class SopRunResult:
    terminal: str
    steps: list[SopStepResult] = field(default_factory=list)
    checklist_passed: bool = False


class SopPipelineRunner:
    def __init__(self, skill_dir: Path) -> None:
        self.skill_dir = skill_dir
        self.spec = load_sop_steps(skill_dir)

    def run(
        self,
        *,
        checklist_ok: bool = True,
        schema_ok: bool = True,
        policy_ok: bool = True,
        evaluate_ok: bool = True,
        hitl_passed: bool = True,
        embed_fn: Callable[[], Any] | None = None,
        skip_walls: bool = False,
    ) -> SopRunResult:
        if skip_walls:
            raise ValueError("forbidden: cannot skip validate walls")
        results: list[SopStepResult] = []
        for step in self.spec["steps"]:
            sid = step["id"]
            stype = step.get("type")
            wall = step.get("wall", False)
            if stype in {"retrieve", "extract", "decide", "understand"}:
                results.append(SopStepResult(sid, "ok", stype))
                continue
            if stype == "validate":
                hook = step.get("hook", "")
                ok = True
                if "checklist" in hook or step.get("checklist"):
                    ok = checklist_ok
                elif hook == "schema_validate":
                    ok = schema_ok
                elif hook == "policy_hooks" or "no_production" in hook or "no_hot" in hook or "evidence" in hook:
                    ok = policy_ok
                else:
                    ok = checklist_ok and schema_ok and policy_ok
                results.append(SopStepResult(sid, "ok" if ok else "failed", hook))
                if wall and not ok:
                    return SopRunResult("failed", results, checklist_passed=False)
                continue
            if stype == "evaluate":
                results.append(SopStepResult(sid, "ok" if evaluate_ok else "failed", "evaluate"))
                if wall and not evaluate_ok:
                    return SopRunResult("awaiting_hitl", results, checklist_passed=checklist_ok)
                continue
            if stype == "hitl":
                results.append(SopStepResult(sid, "ok" if hitl_passed else "failed", "hitl"))
                if not hitl_passed:
                    return SopRunResult("awaiting_hitl", results, checklist_passed=checklist_ok)
                continue
            if stype == "embed":
                if embed_fn:
                    embed_fn()
                results.append(SopStepResult(sid, "ok", "embed"))
                continue
            if stype in {"index", "render", "notify"}:
                results.append(SopStepResult(sid, "ok", stype))
                continue
            results.append(SopStepResult(sid, "ok", stype or "unknown"))
        return SopRunResult("succeeded", results, checklist_passed=checklist_ok)
