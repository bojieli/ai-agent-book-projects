"""Phase 0 pipeline — playbook / SOP / fallback 路由入口。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.events import EventLog
from app.knowledge import KnowledgePlane
from app.planes.pipeline.playbook_executor import (
    run_playbook_pipeline,
    run_safe_fallback,
)
from app.planes.pipeline.sop_executor import run_sop_pipeline
from app.planes.pipeline.step_engine import StepEngine, StepRunState


@dataclass
class MeetingContext:
    meeting_id: str
    org_domains: list[str]
    scenario_type: str
    skill_pack_id: str
    purpose: str
    classification: str = "internal"
    continuum_write_class: str = "wide"
    default_embed_gate: str = "confirm_only"
    production_effect_cap: str = "draft_only"
    maturity: str = "L2"
    series_id: str | None = "series_r1_demo"
    participants: list[str] = field(default_factory=lambda: ["u_dev_a", "u_pm"])
    orchestration_mode: str = "playbook"
    skill_relpath: str = ""
    tool_allowlist: list[str] = field(
        default_factory=lambda: ["connector.defect.create", "connector.task.create"]
    )


@dataclass
class PipelineResult:
    terminal: str
    artifacts: list[dict[str, Any]]
    work_objects: list[dict[str, Any]]
    render: dict[str, Any] | None
    events: list[str]
    traces: int
    usage: dict[str, Any]
    pipeline_path: str = ""
    sop_steps: list[dict[str, str]] = field(default_factory=list)


class Phase0Pipeline:
    def __init__(self, repo_root: Path, knowledge: KnowledgePlane | None = None) -> None:
        self.repo_root = repo_root
        self.engine = StepEngine(repo_root, knowledge=knowledge)
        self.knowledge = self.engine.knowledge
        self.events = self.engine.events

    def begin_run(self) -> None:
        """每次会议流水线独立预算、事件与 trace（Orchestrator 多场景复用时不串台）。"""
        self.engine.begin_run()
        self.events = self.engine.events

    def _to_state(self, meeting: MeetingContext) -> StepRunState:
        return StepRunState(
            meeting_id=meeting.meeting_id,
            org_domains=meeting.org_domains,
            scenario_type=meeting.scenario_type,
            skill_pack_id=meeting.skill_pack_id,
            purpose=meeting.purpose,
            classification=meeting.classification,
            continuum_write_class=meeting.continuum_write_class,
            default_embed_gate=meeting.default_embed_gate,
            production_effect_cap=meeting.production_effect_cap,
            maturity=meeting.maturity,
            series_id=meeting.series_id,
            participants=meeting.participants,
            orchestration_mode=meeting.orchestration_mode,
            tool_allowlist=list(meeting.tool_allowlist),
        )

    def _wrap(self, result: Any) -> PipelineResult:
        self.events = self.engine.events
        return PipelineResult(
            terminal=result.terminal,
            artifacts=result.artifacts,
            work_objects=result.work_objects,
            render=result.render,
            events=result.events,
            traces=result.traces,
            usage=result.usage,
            pipeline_path=result.pipeline_path,
            sop_steps=result.sop_steps,
        )

    def run(
        self,
        meeting: MeetingContext,
        *,
        transcript_ok: bool = True,
        hitl_passed: bool = True,
        artifact_payload: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """按 orchestration_mode 路由到 SOP / Playbook / Fallback。"""
        _ = artifact_payload  # skill pack example 驱动产物，保留参数兼容
        skill_dir = self.repo_root / "app" / "skills" / meeting.skill_relpath
        state = self._to_state(meeting)
        mode = meeting.orchestration_mode

        if meeting.maturity == "L0" or meeting.scenario_type == "unknown":
            out = run_safe_fallback(self.engine, state, skill_dir, hitl_passed=hitl_passed)
        elif mode == "sop":
            out = run_sop_pipeline(
                self.engine, state, skill_dir, hitl_passed=hitl_passed, transcript_ok=transcript_ok
            )
        else:
            out = run_playbook_pipeline(
                self.engine,
                state,
                skill_dir,
                self.repo_root,
                hitl_passed=hitl_passed,
                transcript_ok=transcript_ok,
            )
        return self._wrap(out)
