"""Orchestrator 路由与主路径行为测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.harness import ToolRuntime, idem_key
from app.knowledge import KnowledgePlane
from app.knowledge.series import MeetingSeriesStore, SeriesOpenItem
from app.knowledge.series_bridge import SeriesContinuumBridge
from app.orchestrator import Orchestrator
from app.planes.pipeline.sop_runner import SopPipelineRunner

ROOT = Path(__file__).resolve().parents[2]


def test_orchestrator_sop_routes_to_sop_path():
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    out = orch.bind_and_run(scenario_code="release_review", hitl_passed=True)
    assert out["orchestration_mode"] == "sop"
    assert out["pipeline_path"] == "sop"
    pipe = out["pipeline"]
    assert pipe["terminal"] == "succeeded"
    assert pipe["sop_steps"]
    step_ids = [s["step_id"] for s in pipe["sop_steps"]]
    assert "checklist" in step_ids
    assert "schema_validate" in step_ids
    assert "evaluate" in step_ids


def test_orchestrator_playbook_tech_review():
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    out = orch.bind_and_run(scenario_code="tech_review", hitl_passed=True)
    assert out["orchestration_mode"] == "playbook"
    assert out["pipeline_path"] == "playbook"
    pipe = out["pipeline"]
    assert pipe["terminal"] == "succeeded"
    assert pipe["work_objects"]
    assert pipe["work_objects"][0]["object_type"] == "defect"


def test_orchestrator_unknown_safe_fallback():
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    out = orch.bind_and_run(scenario_code="not_a_real_code", hitl_passed=True)
    assert out["pipeline_path"] == "fallback"
    pipe = out["pipeline"]
    assert pipe["terminal"] == "succeeded"
    assert pipe["work_objects"] == []
    assert "evaluation.passed" in pipe["events"]


def test_hitl_gate_blocks_embed():
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    out = orch.bind_and_run(scenario_code="tech_review", hitl_passed=False)
    pipe = out["pipeline"]
    assert pipe["terminal"] == "awaiting_hitl"
    assert not pipe["work_objects"]
    assert "hitl.requested" in pipe["events"]


def test_idempotent_embed_same_meeting():
    rt = ToolRuntime()
    from app.connectors import MockDefectConnector

    rt.register(MockDefectConnector())
    key = idem_key("mtg_idem", "defect", "同一标题")
    r1 = rt.call(
        "connector.defect.create",
        "mtg_idem",
        {"title": "同一标题"},
        allowlist=["connector.defect.create"],
        max_effect="draft_only",
        effect_rank={"none": 0, "draft_only": 1, "production": 2},
        idempotency_key=key,
    )
    r2 = rt.call(
        "connector.defect.create",
        "mtg_idem",
        {"title": "同一标题"},
        allowlist=["connector.defect.create"],
        max_effect="draft_only",
        effect_rank={"none": 0, "draft_only": 1, "production": 2},
        idempotency_key=key,
    )
    assert r1["external_id"] == r2["external_id"]


def test_continuum_series_bridge_retrievable():
    kp = KnowledgePlane()
    bridge = SeriesContinuumBridge(kp, MeetingSeriesStore())
    bridge.write_open_item(
        series_id="series_test",
        item_id="blk1",
        title="网关容量阻塞未关闭",
        source_meeting_id="mtg_prev",
        org_domain="eng",
        classification="internal",
        write_class="wide",
        acl_principals=["u_pm"],
    )
    hits, _ = kp.retrieve(user_id="u_pm", org_domains=["eng"], query="网关容量阻塞")
    assert any("series_series_test_blk1" in h.id or "网关" in h.text for h in hits)
    brief = bridge.briefing_open_items("series_test", user_id="u_pm", org_domains=["eng"])
    assert brief and brief[0]["title"] == "网关容量阻塞未关闭"


def test_budget_isolation_three_sop_scenarios():
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    codes = ["release_review", "limit_pricing_review", "risk_policy_review"]
    for code in codes:
        out = orch.bind_and_run(scenario_code=code, hitl_passed=True)
        pipe = out["pipeline"]
        assert pipe["terminal"] == "succeeded", (code, pipe["terminal"], pipe.get("events"))
        assert out["pipeline_path"] == "sop"
        assert "evaluation.passed" in pipe["events"]


def test_sop_runner_r4_walls_still_unit_testable():
    runner = SopPipelineRunner(ROOT / "app/skills/eng/R4_release_review")
    ok = runner.run(checklist_ok=True, evaluate_ok=True, hitl_passed=True)
    assert ok.terminal == "succeeded"
    bad = runner.run(checklist_ok=False)
    assert bad.terminal == "failed"
