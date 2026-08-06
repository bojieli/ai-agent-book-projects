"""Orchestrator 多场景连续 bind_and_run 不应串预算/事件。"""

from __future__ import annotations

from pathlib import Path

from app.orchestrator import Orchestrator

ROOT = Path(__file__).resolve().parents[2]


def test_orchestrator_three_sop_scenarios_same_instance():
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    codes = ["release_review", "limit_pricing_review", "risk_policy_review"]
    for code in codes:
        out = orch.bind_and_run(scenario_code=code, hitl_passed=True)
        pipe = out["pipeline"]
        assert pipe["terminal"] == "succeeded", (code, pipe["terminal"], pipe.get("events"))
        assert out["pipeline_path"] == "sop"
        assert "evaluation.passed" in pipe["events"]
    # confirm_only 场景有 work_objects；block gate 场景跳过 embed
    out_r4 = orch.bind_and_run(scenario_code="release_review", hitl_passed=True)
    assert out_r4["pipeline"]["work_objects"]
