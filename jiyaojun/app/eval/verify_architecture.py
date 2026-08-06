"""Architecture v7.7 必做能力 1–17 + Phase0 DoD — executable verification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.agents import Evaluator
from app.connectors import (
    ForbiddenProductionConnector,
    MockDefectConnector,
    MockTaskConnector,
    as_mcp_list,
)
from app.domain_layer import WorkObjectRef, load_or_default, validate_envelope
from app.events import DomainEventType
from app.governance import GovernanceStatus, SkillGovernanceRecord, can_load_in_production
from app.harness import ToolRuntime
from app.knowledge import GlossaryStore, KnowledgePlane
from app.knowledge.transcript import HOTWORD_PROFILES, TranscriptAdapter
from app.observability import BudgetTracker, CostQuota
from app.orchestrator import Orchestrator
from app.policy import AmbiguityService, PolicyBinding, PolicyStore, max_strict_embed_gate
from app.events.enums import PRODUCTION_EFFECT_RANK
from app.render import RenderService
from app.skills_runtime import assert_no_sop_for_playbook, load_sop_steps

SKILLS = ROOT / "app" / "skills"
PASS: list[str] = []
FAIL: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        PASS.append(name)
        print(f"  OK  {name}")
    else:
        FAIL.append(f"{name}: {detail}")
        print(f" FAIL {name}: {detail}")


def verify_1_governance() -> None:
    approved = SkillGovernanceRecord(
        "platform/general@0.1.0", GovernanceStatus.APPROVED, "general", "playbook", "L0"
    )
    draft = SkillGovernanceRecord(
        "eng/R1@0.1.0", GovernanceStatus.DRAFT, "R1", "playbook", "L2"
    )
    check("1.governance_approved_loads", can_load_in_production(approved))
    check("1.governance_draft_blocked", not can_load_in_production(draft))


def verify_2_sop_and_playbook() -> None:
    load_sop_steps(SKILLS / "eng/R4_release_review")
    check("2.sop_r4_loads", True)
    try:
        assert_no_sop_for_playbook(SKILLS / "eng/R1_req_sync")
        check("2b.playbook_no_fake_sop", True)
    except ValueError as e:
        check("2b.playbook_no_fake_sop", False, str(e))
    playbook = yaml.safe_load((ROOT / "app/playbooks/default.yaml").read_text())
    ids = [s["id"] for s in playbook["steps"]]
    check(
        "2b.default_playbook_walls",
        "schema_validate" in ids and "evaluate" in ids and "policy_hooks" in ids,
    )


def verify_3_evaluator() -> None:
    ev = Evaluator()
    bad = {
        "artifact_id": "x",
        "meeting_id": "m",
        # missing required fields
    }
    res = ev.evaluate(artifact=bad)
    check("3.evaluator_rejects_bad_envelope", not res.passed)


def verify_4_5_knowledge() -> None:
    kp = KnowledgePlane()
    kp.seed_demo()
    # ACL: hr user cannot see eng sealed? eng continuum is wide with u_dev_a
    hits_ok, hops = kp.retrieve(user_id="u_dev_a", org_domains=["eng"], query="网关", max_hops=3)
    check("4.knowledge_acl_retrieve", len(hits_ok) >= 1 and hops >= 1)
    hits_deny, _ = kp.retrieve(user_id="stranger", org_domains=["eng"], query="网关", max_hops=3)
    check("4.knowledge_acl_denies_stranger", len(hits_deny) == 0)
    bad = kp.decide_continuum_write(classification="critical", requested_write_class="wide")
    check("4.critical_wide_rejected", not bad.accepted)
    good = kp.decide_continuum_write(classification="critical", requested_write_class="sealed")
    check("4.critical_sealed_ok", good.accepted)
    # agentic hop budget
    _, hops2 = kp.retrieve(user_id="u_dev_a", org_domains=["eng"], query="zzzz_no_match_xxx", max_hops=2)
    check("5.agentic_budget_capped", hops2 <= 2)


def verify_6_mcp() -> None:
    tools = as_mcp_list([MockTaskConnector(), MockDefectConnector()])
    check("6.mcp_descriptors", len(tools) == 2 and all("inputSchema" in t for t in tools))


def verify_7_policy() -> None:
    check("7.embed_gate_max_strict", max_strict_embed_gate("allow", "block") == "block")
    rt = ToolRuntime()
    rt.register(ForbiddenProductionConnector())
    rt.register(MockDefectConnector())
    discovered = rt.discover(
        allowlist=None, max_effect="draft_only", effect_rank=PRODUCTION_EFFECT_RANK
    )
    check("7.production_tool_not_discovered", "connector.policy.production_enable" not in discovered)
    try:
        rt.call(
            "connector.policy.production_enable",
            "m",
            {},
            allowlist=["connector.policy.production_enable"],
            max_effect="draft_only",
            effect_rank=PRODUCTION_EFFECT_RANK,
        )
        check("7.production_call_denied", False, "should raise")
    except PermissionError:
        check("7.production_call_denied", True)


def verify_8_workobject() -> None:
    fields = set(WorkObjectRef.required_fields())
    check("8.workobject_required_fields", fields >= {
        "work_object_id", "connector_id", "org_domain", "object_type",
        "production_effect", "idempotency_key", "meeting_id", "status",
    })


def verify_9_ambiguity() -> None:
    amb = AmbiguityService()
    rec = amb.open(
        "m1",
        "灰度",
        [
            {"sense_id": "eng", "org_domain": "eng", "gloss": "发布"},
            {"sense_id": "biz", "org_domain": "business", "gloss": "客群"},
        ],
    )
    ev = Evaluator()
    art = json.loads((SKILLS / "cross/X1_gray_ambiguity/examples/ruling_envelope.json").read_text())
    # force open ambiguity fake agree
    res = ev.evaluate(artifact=art, ambiguity_open=True, prose_claims_all_agree=True)
    check("9.ambiguity_fake_agree_fails", not res.passed)
    amb.resolve(rec.ambiguity_record_id, "eng", "u_pm")
    check("9.ambiguity_resolve", amb.records[rec.ambiguity_record_id].status == "resolved")


def verify_10_budget() -> None:
    b = BudgetTracker(CostQuota(max_retrieve_hops=1))
    b.charge(retrieve_hops=2)
    check("10.budget_exhausted", "retrieve" in b.exhausted)


def verify_11_eval_gate_skills() -> None:
    # reuse smoke_skills logic lightly
    from app.eval.smoke_skills import V1, _front_matter

    ok = True
    for story, (rel, mode) in V1.items():
        meta = _front_matter((SKILLS / rel / "SKILL.md").read_text(encoding="utf-8"))
        if meta.get("orchestration_mode") != mode:
            ok = False
    check("11.v1_skill_modes", ok)


def verify_12_render_acl_first() -> None:
    svc = RenderService(ROOT / "app/render/default")
    view = svc.materialize_acl_view(
        view_id="v",
        meeting_id="m",
        artifacts=[{"artifact_kind": "draft", "payload": {}, "unresolved": []}],
        viewer_ids=["u1"],
        classification="critical",
        allowlist=None,
    )
    rr = svc.render_email(job_id="j", acl_view=view, classification="critical", allowlist=None)
    check("12.render_critical_skip", rr.status == "skipped" and rr.skip_reason == "critical_no_allowlist")


def verify_13_envelopes() -> None:
    bad = 0
    total = 0
    for p in SKILLS.rglob("examples/*.json"):
        total += 1
        errs = validate_envelope(json.loads(p.read_text(encoding="utf-8")))
        if errs:
            bad += 1
            print("    envelope fail", p, errs[:2])
    check("13.all_example_envelopes", bad == 0, f"{bad}/{total} invalid")


def verify_14_events() -> None:
    required = {
        "meeting.scheduled",
        "transcript.ready",
        "understanding.completed",
        "ambiguity.opened",
        "ambiguity.resolved",
        "artifact.persisted",
        "evaluation.passed",
        "evaluation.failed",
        "hitl.requested",
        "hitl.resolved",
        "work_link.submitted",
        "work_link.synced",
        "continuum.write_decided",
        "render.completed",
        "render.skipped",
        "delivery.sent",
        "delivery.suppressed",
        "pipeline.terminal",
        "budget.exhausted",
        "policy_binding.updated",
    }
    have = {e.value for e in DomainEventType}
    check("14.domain_event_catalog", required <= have, str(required - have))


def verify_15_obs_quota() -> None:
    check("15.cost_quota_type", CostQuota().max_embed_attempts == 3)
    store = PolicyStore()
    store.create_initial(
        PolicyBinding("pb1", "m", 1, "initial", "confirm_only", "internal", "wide", "draft_only")
    )
    store.append_version(
        PolicyBinding("pb2", "m", 2, "pre_embed", "confirm_only", "internal", "wide", "draft_only")
    )
    check("15.policy_binding_immutable_versions", len(store.history("m")) == 2)


def verify_16_transcript_hotwords() -> None:
    ad = TranscriptAdapter()
    doc = ad.ingest_mock("m", ["eng"], ["我们先灰度"])
    check("16.transcript_adapter", doc.segment_count == 1 and doc.hotword_profile_id == "eng_default")
    check(
        "16.no_global_hotword_merge",
        ad.forbid_global_hotword_merge(
            [
                type(HOTWORD_PROFILES["eng_default"])(
                    "ALL", ["eng", "hr", "business"], ["x"]
                )
            ]
        ),
    )
    g = GlossaryStore()
    check(
        "16.glossary_isolation",
        g.isolation_violation("校准", allowed_scopes=["eng"], used_domain="hr") is True,
    )


def verify_17_matrix_registry() -> None:
    reg = load_or_default()
    stories = {s.story_id for s in reg.scenarios.values()}
    need = {"R1", "R4", "R5", "B4", "B5", "H2", "H5", "K1", "K5", "C2", "X1", "general"}
    check("17.v1_matrix_registered", need <= stories, str(need - stories))


def verify_phase0_dod() -> None:
    orch = Orchestrator(ROOT, allow_draft_skills=True)
    out = orch.bind_and_run(scenario_code="tech_review", meeting_id="mtg_dod", hitl_passed=True)
    pipe = out["pipeline"]
    wos = pipe.get("work_objects") or []
    render = pipe.get("render") or {}
    events = pipe.get("events") or []
    ok = (
        pipe.get("terminal") == "succeeded"
        and bool(wos)
        and wos[0].get("object_type") == "defect"
        and render.get("status") == "completed"
        and "evaluation.passed" in events
    )
    check(
        "DoD.eng_tech_review_defect_render",
        ok,
        f"terminal={pipe.get('terminal')} wos={len(wos)} events={events}",
    )


def main() -> int:
    print("=== Architecture capability verification ===")
    verify_1_governance()
    verify_2_sop_and_playbook()
    verify_3_evaluator()
    verify_4_5_knowledge()
    verify_6_mcp()
    verify_7_policy()
    verify_8_workobject()
    verify_9_ambiguity()
    verify_10_budget()
    verify_11_eval_gate_skills()
    verify_12_render_acl_first()
    verify_13_envelopes()
    verify_14_events()
    verify_15_obs_quota()
    verify_16_transcript_hotwords()
    verify_17_matrix_registry()
    verify_phase0_dod()
    print(f"\nPassed {len(PASS)}  Failed {len(FAIL)}")
    for f in FAIL:
        print(" -", f)
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
