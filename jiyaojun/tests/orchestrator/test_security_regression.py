"""P1/P2 安全回归：Continuum/briefing ACL、fail-closed、usage 模拟标注。"""

from __future__ import annotations

from pathlib import Path

from app.knowledge import KnowledgePlane
from app.knowledge.series import MeetingSeriesStore, SeriesOpenItem
from app.knowledge.series_bridge import SeriesContinuumBridge
from app.orchestrator import Orchestrator
from app.planes.dialog import DialogPlane
from app.planes.pipeline.step_engine import StepEngine, StepRunState
from app.skills_runtime.skill_pack import SkillPack

ROOT = Path(__file__).resolve().parents[2]


def test_none_write_class_no_index_no_briefing():
    kp = KnowledgePlane()
    bridge = SeriesContinuumBridge(kp, MeetingSeriesStore())
    # 直接往 store 塞 none 项（模拟错误写入路径）也不应被 sync 索引
    bridge.series.add_open(
        "s_none",
        SeriesOpenItem(
            item_id="n1",
            title="不应出现的 none 项",
            org_domain="eng",
            classification="internal",
            write_class="none",
            acl_principals=["u_pm"],
        ),
    )
    indexed = bridge.sync_open_items_to_continuum("s_none", write_class="none")
    assert indexed == 0
    assert not any("s_none" in c.id for c in kp.continuum)
    brief = bridge.briefing_open_items("s_none", user_id="u_pm", org_domains=["eng"])
    assert brief == []


def test_critical_wide_rejected_not_in_store():
    kp = KnowledgePlane()
    bridge = SeriesContinuumBridge(kp, MeetingSeriesStore())
    ok = bridge.write_open_item(
        series_id="s_crit",
        item_id="leak",
        title="机密组织调整摘要",
        source_meeting_id="mtg_h5",
        org_domain="hr",
        classification="critical",
        write_class="wide",
        acl_principals=["u_hrbp"],
    )
    assert ok is False
    assert bridge.series.list_open("s_crit") == []
    brief = bridge.briefing_open_items("s_crit", user_id="u_hrbp", org_domains=["hr"])
    assert brief == []


def test_non_acl_user_series_open_count_zero():
    kp = KnowledgePlane()
    kp.seed_demo()
    dialog = DialogPlane(kp)
    # series_pay 有 eng open item，u_pm 可见
    brief_pm = dialog.briefing(
        user_id="u_pm",
        org_domains=["eng"],
        query="网关",
        series_id="series_pay",
        classification="internal",
        continuum_write_class="wide",
    )
    assert brief_pm.series_open_count >= 1
    # stranger 无 ACL
    brief_str = dialog.briefing(
        user_id="stranger",
        org_domains=["eng"],
        query="网关",
        series_id="series_pay",
        classification="internal",
        continuum_write_class="wide",
    )
    assert brief_str.series_open_count == 0


def test_critical_sealed_only_acl_principal():
    kp = KnowledgePlane()
    bridge = SeriesContinuumBridge(kp, MeetingSeriesStore())
    bridge.write_open_item(
        series_id="s_sealed",
        item_id="org",
        title="组织调整密封摘要",
        source_meeting_id="mtg_h5",
        org_domain="hr",
        classification="critical",
        write_class="sealed",
        acl_principals=["u_hrbp"],
    )
    assert bridge.briefing_open_items("s_sealed", user_id="u_hrbp", org_domains=["hr"])
    assert bridge.briefing_open_items("s_sealed", user_id="u_pm", org_domains=["hr"]) == []
    assert bridge.briefing_open_items("s_sealed", user_id="u_hrbp", org_domains=["eng"]) == []


def test_unknown_step_type_fails_closed():
    engine = StepEngine(ROOT)
    pack = SkillPack.load(ROOT / "app/skills/eng/R1_req_sync")
    meeting = StepRunState(
        meeting_id="mtg_bad_step",
        org_domains=["eng"],
        scenario_type="tech_review",
        skill_pack_id="eng/R1@0.1.0",
        purpose="test",
        tool_allowlist=["connector.defect.create"],
    )
    result = engine.run_from_spec(
        meeting,
        skill_pack=pack,
        steps=[
            {"id": "understand", "type": "understand"},
            {"id": "bogus", "type": "teleport"},
        ],
    )
    assert result.terminal == "failed"
    assert any(s["detail"].startswith("unknown_step_type") for s in result.sop_steps)


def test_unknown_validate_hook_fails_closed():
    engine = StepEngine(ROOT)
    pack = SkillPack.load(ROOT / "app/skills/eng/R1_req_sync")
    meeting = StepRunState(
        meeting_id="mtg_bad_hook",
        org_domains=["eng"],
        scenario_type="tech_review",
        skill_pack_id="eng/R1@0.1.0",
        purpose="test",
        tool_allowlist=["connector.defect.create"],
    )
    art = pack.build_artifact(
        meeting_id=meeting.meeting_id,
        scenario_type=meeting.scenario_type,
        skill_pack_id=meeting.skill_pack_id,
        org_domains=meeting.org_domains,
        classification=meeting.classification,
        continuum_write_class=meeting.continuum_write_class,
    )
    result = engine.run_from_spec(
        meeting,
        skill_pack=pack,
        steps=[
            {"id": "understand", "type": "understand"},
            {"id": "artifact", "type": "artifact"},
            {
                "id": "mystery",
                "type": "validate",
                "hook": "not_a_real_hook",
                "wall": True,
            },
        ],
    )
    assert result.terminal == "failed"
    assert any("unknown_hook" in s["detail"] for s in result.sop_steps)


def test_unknown_embed_tool_fails_closed():
    engine = StepEngine(ROOT)
    pack = SkillPack.load(ROOT / "app/skills/eng/R1_req_sync")
    meeting = StepRunState(
        meeting_id="mtg_bad_tool",
        org_domains=["eng"],
        scenario_type="tech_review",
        skill_pack_id="eng/R1@0.1.0",
        purpose="test",
        maturity="L2",
        default_embed_gate="allow",
        tool_allowlist=["connector.defect.create"],
    )
    result = engine.run_from_spec(
        meeting,
        skill_pack=pack,
        steps=[
            {"id": "understand", "type": "understand"},
            {"id": "retrieve", "type": "retrieve"},
            {"id": "artifact", "type": "artifact"},
            {"id": "schema_validate", "type": "validate", "hook": "schema_validate", "wall": True},
            {"id": "policy_hooks", "type": "validate", "hook": "policy_hooks", "wall": True},
            {"id": "evaluate", "type": "evaluate", "wall": True},
            {"id": "hitl", "type": "hitl"},
            {
                "id": "embed",
                "type": "embed",
                "tools": ["connector.unknown.foo"],
            },
        ],
        hitl_passed=True,
    )
    assert result.terminal == "failed"
    assert any("unknown" in s["detail"] for s in result.sop_steps if s["step_id"] == "embed")


def test_declared_tool_embed_succeeds():
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    out = orch.bind_and_run(scenario_code="tech_review", hitl_passed=True)
    assert out["pipeline"]["terminal"] == "succeeded"
    assert out["pipeline"]["work_objects"]
    assert out["pipeline"]["work_objects"][0]["connector_id"] == "connector.defect.create"


def test_usage_marked_simulated():
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    out = orch.bind_and_run(scenario_code="tech_review", hitl_passed=True)
    usage = out["pipeline"]["usage"]
    assert usage.get("measurement_mode") == "simulated"
    assert "llm_tokens_simulated" in usage
    assert "llm_tokens" not in usage or usage.get("llm_tokens") is None
