"""Story family gates (Ch6) — 故事族门禁，接 run_all。"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agents.evaluator import Evaluator
from app.agents.artifact_agent import ArtifactAgent
from app.knowledge import KnowledgePlane
from app.knowledge.series import MeetingSeriesStore
from app.knowledge.series_bridge import SeriesContinuumBridge
from app.orchestrator import Orchestrator
from app.planes.dialog import DialogPlane
from app.planes.pipeline.step_engine import StepEngine, StepRunState
from app.policy import AmbiguityService
from app.skills_runtime.skill_pack import SkillPack
from app.skills_runtime.sop_loader import load_sop_steps


@dataclass
class GateResult:
    gate_id: str
    story_id: str
    passed: bool
    detail: str = ""


@dataclass
class StoryGateReport:
    results: list[GateResult] = field(default_factory=list)
    report_path: Path | None = None

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    def to_json(self) -> str:
        return json.dumps(
            {
                "passed": self.passed,
                "total": len(self.results),
                "failed": [r.__dict__ for r in self.results if not r.passed],
                "results": [r.__dict__ for r in self.results],
                "report_path": str(self.report_path) if self.report_path else None,
            },
            ensure_ascii=False,
            indent=2,
        )

    def write_report(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        self.report_path = path


def _load_gates(path: Path) -> list[dict[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("gates") or [])


def _parse_hits(detail: str) -> int:
    m = re.search(r"hits=(\d+)", detail or "")
    return int(m.group(1)) if m else 0


def _citation_leaks_sealed(citations: list[dict[str, Any]]) -> int:
    """按真实 citation/source 字段检测 critical/sealed 泄露。"""
    leaks = 0
    for c in citations:
        cls = str(c.get("classification", ""))
        wc = str(c.get("write_class", ""))
        preview = str(c.get("text_preview", ""))
        source = str(c.get("source_id", "") or c.get("id", ""))
        if cls == "critical" or wc == "sealed":
            leaks += 1
        elif "密封" in preview or "密封" in source:
            leaks += 1
    return leaks


def _run_check(check: dict[str, Any], ctx: dict[str, Any]) -> tuple[bool, str]:
    ctype = check["type"]
    out = ctx.get("orch_out") or {}
    pipe = out.get("pipeline") or {}

    if ctype == "must_recall":
        steps = pipe.get("sop_steps") or []
        sid = check.get("contains_step", "")
        step = next((s for s in steps if s.get("step_id") == sid), None)
        if not step:
            return False, f"step {sid} missing in {[s.get('step_id') for s in steps]}"
        if step.get("status") != "ok":
            return False, f"step {sid} status={step.get('status')}"
        hits = _parse_hits(str(step.get("detail", "")))
        min_hits = check.get("min_hits", 1)
        if hits < min_hits:
            return False, f"step {sid} hits={hits} need>={min_hits}"
        briefing_hits = out.get("briefing_hits", 0)
        if briefing_hits < min_hits:
            return False, f"briefing_hits={briefing_hits} need>={min_hits}"
        return True, f"step {sid} hits={hits} briefing_hits={briefing_hits}"

    if ctype == "briefing_series":
        bc = ctx.get("briefing_open_count", 0)
        need = check.get("min_open_count", 1)
        return bc >= need, f"briefing_open_count={bc} need>={need}"

    if ctype == "sop_wall":
        steps = {s.get("step_id") for s in (pipe.get("sop_steps") or [])}
        req = set(check.get("required_steps") or [])
        ok = req <= steps
        return ok, f"missing {req - steps}"

    if ctype == "sop_wall_blocks_on_failure":
        skill_dir = ROOT / check["skill_dir"]
        engine = StepEngine(ROOT)
        pack = SkillPack.load(skill_dir)
        spec = load_sop_steps(skill_dir)
        meeting = StepRunState(
            meeting_id="r4_gate_neg",
            org_domains=["eng"],
            scenario_type="release_review",
            skill_pack_id=f"{pack.meta.get('skill_pack_id', 'eng/R4_release_review@0.1.0')}",
            purpose="r4 wall negative",
            maturity="L3",
            force_validate_fail={"checklist"},
        )
        bad = engine.run_from_spec(meeting, skill_pack=pack, steps=spec["steps"], hitl_passed=True)
        chk = next((s for s in bad.sop_steps if s.get("step_id") == "checklist"), None)
        ok = bad.terminal == "failed" and chk and chk.get("status") == "failed"
        return ok, f"StepEngine terminal={bad.terminal} checklist={chk}"

    if ctype == "pipeline_path":
        expect = check.get("expect", "")
        got = out.get("pipeline_path", "")
        return got == expect, f"path={got} expect={expect}"

    if ctype == "must_not_leak":
        cnt = ctx.get("leak_open_count", 0)
        rag_leak = ctx.get("rag_citation_leak_count", 0)
        mx = check.get("max_open_count", 0)
        ok = cnt <= mx and rag_leak <= mx
        return ok, f"series_leak={cnt} rag_leak={rag_leak} max={mx}"

    if ctype == "embed_gate":
        wos = pipe.get("work_objects") or []
        if check.get("expect_no_work_objects"):
            return len(wos) == 0, f"work_objects={len(wos)}"
        return bool(wos), f"work_objects={len(wos)}"

    if ctype == "unknown_fallback":
        path = out.get("pipeline_path", "")
        expect = check.get("pipeline_path", "fallback")
        wos = pipe.get("work_objects") or []
        ok = path == expect and (not check.get("expect_no_work_objects") or len(wos) == 0)
        return ok, f"path={path} wos={len(wos)}"

    if ctype == "x1_unresolved_no_writeback":
        amb = AmbiguityService()
        amb.open(
            "x1_gate",
            "灰度",
            [
                {"sense_id": "a", "org_domain": "eng", "gloss": "x"},
                {"sense_id": "b", "org_domain": "business", "gloss": "y"},
            ],
        )
        art = ArtifactAgent().build_action_items_envelope(
            meeting_id="x1_gate",
            org_domains=["eng", "business"],
            scenario_type="cross_req_align",
            skill_pack_id="cross/X1@0.1.0",
            segments=["各方同意"],
        )
        res = Evaluator().evaluate(artifact=art, ambiguity_open=True, prose_claims_all_agree=True)
        direct_blocked = not res.passed

        orch = ctx.get("orch")
        orch_blocked = False
        orch_detail = "orch_skipped"
        if orch is not None:
            mid = check.get("meeting_id", "mtg_x1_gate")
            orch.pipeline.engine.ambiguity.open(
                mid,
                "灰度",
                [
                    {"sense_id": "a", "org_domain": "eng", "gloss": "x"},
                    {"sense_id": "b", "org_domain": "business", "gloss": "y"},
                ],
            )
            out = orch.bind_and_run(scenario_code="cross_req_align", meeting_id=mid, hitl_passed=True)
            pipe = out.get("pipeline") or {}
            wos = pipe.get("work_objects") or []
            orch_blocked = pipe.get("terminal") != "succeeded" and len(wos) == 0
            embed_step = next((s for s in pipe.get("sop_steps") or [] if s.get("step_id") == "embed"), None)
            orch_detail = (
                f"terminal={pipe.get('terminal')} wos={len(wos)} embed={embed_step}"
            )

        ok = direct_blocked and orch_blocked
        return ok, f"eval_passed={res.passed} orch={orch_detail}"

    return False, f"unknown check type {ctype}"


def run_story_gates(
    gates_path: Path | None = None,
    *,
    report_path: Path | None = None,
) -> StoryGateReport:
    path = gates_path or ROOT / "fixtures/eval/story_gates.yaml"
    gates = _load_gates(path)
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    report = StoryGateReport()

    kp = KnowledgePlane()
    kp.seed_demo()
    bridge = SeriesContinuumBridge(kp, MeetingSeriesStore())
    bridge.write_open_item(
        series_id="series_h5_test",
        item_id="sealed1",
        title="组织调整密封",
        source_meeting_id="mtg_h5",
        org_domain="hr",
        classification="critical",
        write_class="sealed",
        acl_principals=["u_hrbp"],
    )
    dialog = DialogPlane(kp)

    for gate in gates:
        gid = gate["id"]
        story = gate["story_id"]
        code = gate["scenario_code"]
        ctx: dict[str, Any] = {"orch": orch}

        if story == "H5":
            brief = dialog.briefing(
                user_id="u_pm",
                org_domains=["hr"],
                query="组织",
                series_id="series_h5_test",
                classification="critical",
                continuum_write_class="sealed",
            )
            ctx["leak_open_count"] = brief.series_open_count
            reply = dialog.ask(
                user_id="u_pm",
                org_domains=["hr"],
                query="组织调整密封细节",
            )
            ctx["rag_citation_leak_count"] = _citation_leaks_sealed(reply.citations)
            out = orch.bind_and_run(scenario_code=code, hitl_passed=True)
            ctx["orch_out"] = out
        elif story == "R5":
            out = orch.bind_and_run(scenario_code=code, hitl_passed=True, series_id="series_pay")
            ctx["orch_out"] = out
            ctx["briefing_open_count"] = out.get("briefing_series_open", 0)
        elif story == "X1":
            out = orch.bind_and_run(scenario_code=code, hitl_passed=True)
            ctx["orch_out"] = out
        else:
            out = orch.bind_and_run(scenario_code=code, hitl_passed=True)
            ctx["orch_out"] = out

        ok_all = True
        details: list[str] = []
        for chk in gate.get("checks") or []:
            ok, det = _run_check(chk, ctx)
            if not ok:
                ok_all = False
            details.append(f"{chk['type']}:{det}")

        report.results.append(
            GateResult(gate_id=gid, story_id=story, passed=ok_all, detail="; ".join(details))
        )

    out_path = report_path or ROOT / "fixtures/eval/story_gates_report.json"
    report.write_report(out_path)
    return report


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    report = run_story_gates(path)
    print(report.to_json())
    if report.passed:
        print("STORY_GATES_PASSED")
        return 0
    print("STORY_GATES_FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
