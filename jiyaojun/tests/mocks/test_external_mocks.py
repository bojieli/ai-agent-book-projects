"""Mocks for post-phase externals: LLM eval / ASR / vector / Jira / WeCom / backlog packs."""

from __future__ import annotations

from pathlib import Path

from app.agents.llm_evaluator import IndependentLLMEvaluator, MockLLMClient
from app.connectors.mock_saas import MockJiraConnector, MockWeComClient
from app.connectors.persistent_defect import PersistentDefectConnector
from app.governance import GovernanceStatus, SkillGovernanceRecord, can_load_in_production
from app.knowledge.asr import MockAsrService
from app.knowledge.vector_mock import MockHybridIndex, VectorDoc
from app.runtime.mocked_platform import MockedPlatform
from app.skills_runtime.sop_loader import assert_no_sop_for_playbook

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "app" / "skills"


def test_mock_llm_evaluator_pass_and_fail():
    ev = IndependentLLMEvaluator(MockLLMClient())
    art = {
        "artifact_id": "a",
        "meeting_id": "m",
        "org_domains": ["eng"],
        "scenario_type": "tech_review",
        "skill_pack_id": "eng/R1_req_sync@0.1.0",
        "artifact_kind": "action_items",
        "schema_id": "action_items",
        "schema_version": "1.0.0",
        "payload": {"items": [{"title": "补文档", "status": "committed"}]},
        "confidence": "med",
        "unresolved": [],
        "source_spans": [],
        "references": [],
        "classification": "internal",
        "continuum_write_class": "wide",
        "created_by_stage": "artifact",
    }
    ok = ev.evaluate(artifact=art, success_criteria=["actions"], require_llm=True)
    assert ok.passed
    assert "mock_llm_evaluator" in ok.checks
    bad = ev.evaluate(
        artifact=art,
        success_criteria=["actions"],
        ambiguity_open=True,
        prose_claims_all_agree=True,
        require_llm=True,
    )
    # rule layer already fails; llm also sees 各方同意 if we put in payload
    art2 = dict(art)
    art2["payload"] = {"items": [{"title": "各方同意上线", "status": "committed"}]}
    bad2 = ev.evaluate(artifact=art2, success_criteria=["x"], require_llm=True)
    assert bad2.passed is False


def test_mock_asr_domain_hotwords():
    asr = MockAsrService()
    doc = asr.transcribe(
        meeting_id="m_asr",
        org_domains=["eng"],
        audio_object_key="s3://mock/audio.wav",
        raw_utterances=["先会度再观察", "准备回滚兰"],
    )
    assert "灰度" in doc.segments[0]["text"]
    assert doc.hotword_profile_id == "eng_default"
    try:
        asr.assert_no_all_domain_hotword_dump(["ALL"])
        assert False
    except ValueError:
        pass


def test_mock_hybrid_vector_acl_first():
    idx = MockHybridIndex()
    idx.upsert(VectorDoc("a", "eng", "internal", ["u_pm"], "超时重试"))
    idx.upsert(VectorDoc("b", "hr", "critical", ["u_hrbp"], "绩效校准", write_class="sealed"))
    hits = idx.search(query="超时", user_id="u_pm", org_domains=["eng"])
    assert hits and hits[0]["doc_id"] == "a"
    denied = idx.search(query="绩效", user_id="u_pm", org_domains=["hr"])
    assert denied == []


def test_mock_jira_and_wecom(tmp_path: Path):
    defect = PersistentDefectConnector(tmp_path / "d.json")
    jira = MockJiraConnector(defect)
    issue = jira.execute({"title": "超时缺陷", "idempotency_key": "j1", "project": "ENG"})
    assert issue["jira_key"].startswith("ENG-")
    assert "jira.mock.local" in issue["self"]
    wx = MockWeComClient()
    r = wx.send_markdown(touser=["u_pm"], content="**纪要**", meeting_id="m1")
    assert r["ok"] and wx.sent


def test_mocked_platform_e2e(tmp_path: Path):
    plat = MockedPlatform(ROOT, tmp_path / "plat")
    out = plat.runtime.run_meeting_lifecycle(
        event_id="cal_eng_001",
        purpose="需求澄清接口超时",
        idempotency_key=f"mockplat-{tmp_path.name}",
        user_id="u_pm",
        segments=["你补齐超时和重试约定"],
        hitl_approve=True,
    )
    assert out["stage"] == "succeeded"
    # hybrid retrieve
    hits = plat.vectors.search(query="超时", user_id="u_pm", org_domains=["eng"])
    assert hits
    # wecom delivery mock
    sent = plat.deliver_via_wecom(out["meeting_id"], ["u_pm"], "# 纪要\n已同步缺陷")
    assert sent["ok"]
    # jira shape
    j = plat.jira.execute(
        {"title": "from platform", "idempotency_key": f"jira-{tmp_path.name}"}
    )
    assert j["jira_key"]


def test_backlog_stubs_exist_playbook_only_and_draft_blocked():
    backlog = [
        "eng/R2_tech_design",
        "eng/R3_incident_retro",
        "eng/R6_resource_plan",
        "business/B1_ops_sync",
        "hr/H3_comp_review",
        "risk/K2_fp_retro",
        "compliance/C1_policy_align",
        "cross/X2_launch_warroom",
    ]
    for rel in backlog:
        base = SKILLS / rel
        assert (base / "SKILL.md").exists(), rel
        assert_no_sop_for_playbook(base)
        text = (base / "SKILL.md").read_text(encoding="utf-8")
        assert "orchestration_mode: playbook" in text
        assert "governance_status: draft" in text
    # production load blocked
    rec = SkillGovernanceRecord(
        "eng/R2_tech_design@0.1.0",
        GovernanceStatus.DRAFT,
        "R2",
        "playbook",
        "L2",
    )
    assert can_load_in_production(rec) is False
