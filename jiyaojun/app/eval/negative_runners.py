"""Executable runners for fixtures/eval/negative_catalog.yaml（M6 扩充）。"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.agents.evaluator import Evaluator
from app.knowledge import KnowledgePlane
from app.policy import AmbiguityService
from app.render import RenderService
from app.skills_runtime import assert_no_sop_for_playbook
from app.safety.decisions import is_executable
from app.safety.dual_authz import authorize_tool_dual
from app.safety.egress import evaluate_egress
from app.safety.offline import OfflineSafetyGateway
from app.safety.budget import ModelBudgetTracker
from app.knowledge.embedding import BgeM3ShimProvider
from app.knowledge.rag import RagPipeline


ROOT = Path(__file__).resolve().parents[2]


def _rag_empty(query: str, user_id: str, org_domains: list[str]) -> bool:
    rag = RagPipeline(BgeM3ShimProvider())
    rag.index_doc(
        doc_id="doc_pol",
        org_domain="risk",
        classification="confidential",
        acl_principals=["u_risk_pm"],
        title="策略",
        body="策略 pol_fraud_rule_88 Shadow",
    )
    rag.index_doc(
        doc_id="doc_hr",
        org_domain="hr",
        classification="critical",
        acl_principals=["u_hrbp"],
        title="组织调整",
        body="组织调整密封",
        write_class="sealed",
    )
    rag.index_doc(
        doc_id="doc_biz",
        org_domain="business",
        classification="confidential",
        acl_principals=["u_biz_pm"],
        title="限价",
        body="限价双签",
    )
    res = rag.retrieve(query=query, user_id=user_id, org_domains=org_domains, top_k=5)
    return len(res.hits) == 0


def run_negative_catalog() -> list[tuple[str, bool, str]]:
    cat = yaml.safe_load((ROOT / "fixtures/eval/negative_catalog.yaml").read_text())
    results: list[tuple[str, bool, str]] = []
    for item in cat["catalog"]:
        cid = item["id"]
        try:
            if cid == "continuum_wide_leak":
                kp = KnowledgePlane()
                d = kp.decide_continuum_write(classification="critical", requested_write_class="wide")
                assert not d.accepted
            elif cid == "sop_skip_step":
                from app.planes.pipeline.sop_runner import SopPipelineRunner

                runner = SopPipelineRunner(ROOT / "app/skills/eng/R4_release_review")
                try:
                    runner.run(skip_walls=True)
                    raise AssertionError("should forbid skip")
                except ValueError:
                    pass
            elif cid == "empty_shell_sop":
                assert_no_sop_for_playbook(ROOT / "app/skills/eng/R1_req_sync")
            elif cid == "K5_hot_swap":
                assert (ROOT / "app/skills/risk/K5_model_monitor/sop/checklists/no_hot_swap.yaml").exists()
            elif cid == "H5_broadcast":
                svc = RenderService(ROOT / "app/render/default")
                view = svc.materialize_acl_view(
                    view_id="v",
                    meeting_id="m",
                    artifacts=[{}],
                    viewer_ids=["u"],
                    classification="critical",
                    allowlist=None,
                )
                rr = svc.render_email(job_id="j", acl_view=view, classification="critical", allowlist=None)
                assert rr.status == "skipped"
            elif cid == "X1_unresolved_agree":
                amb = AmbiguityService()
                amb.open(
                    "m",
                    "灰度",
                    [
                        {"sense_id": "a", "org_domain": "eng", "gloss": "x"},
                        {"sense_id": "b", "org_domain": "business", "gloss": "y"},
                    ],
                )
                from app.agents.artifact_agent import ArtifactAgent

                art = ArtifactAgent().build_action_items_envelope(
                    meeting_id="m",
                    org_domains=["eng", "business"],
                    scenario_type="cross_req_align",
                    skill_pack_id="cross/X1@0.1.0",
                    segments=["各方同意"],
                )
                res = Evaluator().evaluate(
                    artifact=art, ambiguity_open=True, prose_claims_all_agree=True
                )
                assert not res.passed
            elif cid == "render_full_then_filter":
                svc = RenderService(ROOT / "app/render/default")
                view = svc.materialize_acl_view(
                    view_id="v2",
                    meeting_id="m2",
                    artifacts=[{"payload": {"secret": "x"}}],
                    viewer_ids=["u"],
                    classification="critical",
                    allowlist=None,
                )
                assert view.empty
            elif cid == "global_hotword_force":
                from app.knowledge.asr import MockAsrService

                try:
                    MockAsrService.assert_no_all_domain_hotword_dump(["ALL"])
                    raise AssertionError("should fail")
                except ValueError:
                    pass
            elif cid == "acl_stranger_retrieve":
                assert _rag_empty("限价", "stranger", ["business"])
            elif cid == "sealed_egress_block":
                eg = evaluate_egress(classification="critical", text="密封内容")
                assert eg.allowed is False
            elif cid == "cross_org_retrieve":
                assert _rag_empty("pol_fraud", "u_pm", ["risk"])
            elif cid == "confidential_to_public_user":
                assert _rag_empty("限价", "u_pm", ["business"])
            elif cid == "hr_sealed_to_dev":
                assert _rag_empty("组织调整", "u_dev_a", ["hr"])
            elif cid == "tool_denylist_shell":
                dual = authorize_tool_dual(
                    OfflineSafetyGateway(),
                    tool_id="shell_exec",
                    arguments={},
                    granted_ids=["shell_exec"],
                )
                assert dual.allowed is False
            elif cid == "business_deny_overrides_safety_allow":
                dual = authorize_tool_dual(
                    OfflineSafetyGateway(),
                    tool_id="connector.defect.create",
                    arguments={"title": "x"},
                    granted_ids=[],
                )
                assert dual.allowed is False and dual.reason == "business_denied"
            elif cid == "confirm_only_no_execute":
                assert is_executable("confirm_only") is False
            elif cid == "cross_domain_writeback_blocked":
                amb = AmbiguityService()
                amb.open(
                    "m_x",
                    "灰度",
                    [
                        {"sense_id": "a", "org_domain": "eng", "gloss": "x"},
                        {"sense_id": "b", "org_domain": "business", "gloss": "y"},
                    ],
                )
                assert any(r.meeting_id == "m_x" and r.status == "open" for r in amb.records.values())
            elif cid == "critical_render_skipped":
                svc = RenderService(ROOT / "app/render/default")
                view = svc.materialize_acl_view(
                    view_id="v3",
                    meeting_id="m3",
                    artifacts=[{}],
                    viewer_ids=["u"],
                    classification="critical",
                    allowlist=None,
                )
                rr = svc.render_email(job_id="j3", acl_view=view, classification="critical", allowlist=None)
                assert rr.status == "skipped"
            elif cid == "risk_doc_cross_leak":
                assert _rag_empty("pol_fraud_rule_88", "u_pm", ["risk"])
            elif cid == "sealed_continuum_none":
                kp = KnowledgePlane()
                d = kp.decide_continuum_write(
                    classification="internal", requested_write_class="none"
                )
                assert d.accepted is False
                assert d.rejected_reason == "write_class_none"
            elif cid == "acl_empty_allowlist_deny":
                from app.connectors.discovery import ConnectorCatalog, ToolDiscoveryService
                from app.connectors.mock import MockDefectConnector

                catalog = ConnectorCatalog()
                catalog.register_from_connector(
                    MockDefectConnector(), org_domains=["eng"], scenarios=["*"]
                )
                disc = ToolDiscoveryService(catalog=catalog, min_score=1.0)
                grant = disc.discover(
                    need="建缺陷",
                    org_domains=["eng"],
                    scenario="tech_review",
                    max_effect="draft_only",
                    tool_allowlist=[],
                )
                assert grant.granted_ids == []
            elif cid == "budget_blocks_writeback":
                budget = ModelBudgetTracker(daily_call_limit=1)
                budget.daily_calls = 1
                out = OfflineSafetyGateway(budget=budget).chat_completions(
                    messages=[{"role": "user", "content": "x"}],
                    classification="public",
                )
                assert out.decision == "block"
            else:
                results.append((cid, False, "unknown case"))
                continue
            results.append((cid, True, "ok"))
        except Exception as exc:  # noqa: BLE001
            results.append((cid, False, str(exc)))
    return results
