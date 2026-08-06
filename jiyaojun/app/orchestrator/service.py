"""Thin orchestrator — bind scenario, freeze policy, route pipeline by orchestration_mode."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain_layer import load_or_default
from app.events import DomainEvent, DomainEventType
from app.governance import GovernanceStatus, SkillGovernanceRecord, can_load_in_production
from app.knowledge import KnowledgePlane
from app.planes.dialog import DialogPlane
from app.planes.pipeline.phase0 import MeetingContext, Phase0Pipeline, PipelineResult
from app.policy import PolicyBinding, PolicyStore, max_strict_embed_gate


@dataclass
class Orchestrator:
    root: Path
    allow_draft_skills: bool = True  # Phase0 demo; production must be False

    def __post_init__(self) -> None:
        self.registry = load_or_default()
        self.policy_store = PolicyStore()
        self.knowledge = KnowledgePlane()
        self.knowledge.seed_demo()
        self.dialog = DialogPlane(self.knowledge)
        self.pipeline = Phase0Pipeline(self.root, knowledge=self.knowledge)

    def bind_and_run(
        self,
        *,
        scenario_code: str,
        meeting_id: str | None = None,
        user_id: str = "u_pm",
        hitl_passed: bool = True,
        governance: SkillGovernanceRecord | None = None,
        series_id: str | None = None,
    ) -> dict[str, Any]:
        scenario = self.registry.get_scenario(scenario_code)
        mid = meeting_id or f"mtg_{scenario.story_id.lower()}_{uuid.uuid4().hex[:6]}"

        gov = governance or SkillGovernanceRecord(
            skill_pack_id=f"{scenario.skill_relpath}@0.1.0",
            status=GovernanceStatus.DRAFT,
            story_id=scenario.story_id,
            orchestration_mode=scenario.orchestration_mode,
            maturity_level=scenario.maturity_level,
        )
        if not self.allow_draft_skills and not can_load_in_production(gov):
            raise PermissionError("draft skill cannot load in production pipeline")

        binding = PolicyBinding(
            policy_binding_id=f"pb_{mid}_v1",
            meeting_id=mid,
            version=1,
            reason="initial",
            embed_gate=scenario.default_embed_gate,
            classification=scenario.classification,
            continuum_write_class=scenario.continuum_write_class,
            production_effect_cap=scenario.production_effect_cap,
            glossary_scopes=[scenario.org_domain],
            tool_allowlist=["connector.defect.create", "connector.task.create"],
        )
        self.policy_store.create_initial(binding)
        self.pipeline.events.emit(
            DomainEvent(
                DomainEventType.POLICY_BINDING_UPDATED,
                mid,
                {
                    "policy_binding_id": binding.policy_binding_id,
                    "version": 1,
                    "reason": "initial",
                },
                producer="orchestrator",
            )
        )

        org_domains = [scenario.org_domain] if scenario.story_id != "X1" else ["eng", "business"]
        sid = series_id or ("series_pay" if scenario.story_id in {"R1", "R4", "R5"} else None)
        briefing = self.dialog.briefing(
            user_id=user_id,
            org_domains=org_domains,
            query="超时 阻塞 灰度",
            series_id=sid,
            classification=scenario.classification,
            continuum_write_class=scenario.continuum_write_class,
        )

        self.pipeline.begin_run()

        meeting = MeetingContext(
            meeting_id=mid,
            org_domains=org_domains,
            scenario_type=scenario.code,
            skill_pack_id=f"{scenario.skill_relpath}@0.1.0",
            purpose=f"{scenario.story_id} {scenario.code}",
            classification=scenario.classification,
            continuum_write_class=scenario.continuum_write_class,
            default_embed_gate=scenario.default_embed_gate,
            production_effect_cap=scenario.production_effect_cap,
            maturity=scenario.maturity_level,
            orchestration_mode=scenario.orchestration_mode,
            skill_relpath=scenario.skill_relpath,
            series_id=sid,
            tool_allowlist=list(binding.tool_allowlist),
        )
        result: PipelineResult = self.pipeline.run(meeting, hitl_passed=hitl_passed)

        # pre_embed freeze if succeeded embed path
        if result.terminal == "succeeded" and result.work_objects:
            cur = self.policy_store.current(mid)
            assert cur
            v2 = PolicyBinding(
                policy_binding_id=f"pb_{mid}_v2",
                meeting_id=mid,
                version=2,
                reason="pre_embed",
                embed_gate=max_strict_embed_gate(cur.embed_gate),
                classification=cur.classification,
                continuum_write_class=cur.continuum_write_class,
                production_effect_cap=cur.production_effect_cap,
                glossary_scopes=list(cur.glossary_scopes),
                tool_allowlist=list(cur.tool_allowlist),
            )
            self.policy_store.append_version(v2)
            self.pipeline.events.emit(
                DomainEvent(
                    DomainEventType.POLICY_BINDING_UPDATED,
                    mid,
                    {
                        "policy_binding_id": v2.policy_binding_id,
                        "version": 2,
                        "reason": "pre_embed",
                    },
                    producer="orchestrator",
                )
            )

        return {
            "meeting_id": mid,
            "scenario": scenario.code,
            "orchestration_mode": scenario.orchestration_mode,
            "pipeline_path": result.pipeline_path,
            "briefing_hops": briefing.retrieve_hops,
            "briefing_hits": len(briefing.hits),
            "briefing_series_open": briefing.series_open_count,
            "pipeline": {
                "terminal": result.terminal,
                "events": result.events,
                "work_objects": result.work_objects,
                "render": result.render,
                "usage": result.usage,
                "traces": result.traces,
                "sop_steps": result.sop_steps,
            },
            "policy_versions": [b.version for b in self.policy_store.history(mid)],
        }
