"""Phase 2: Understanding / glossary isolation / Artifact map-reduce / ambiguity."""

from __future__ import annotations

from app.agents.artifact_agent import ArtifactAgent
from app.agents.evaluator import Evaluator
from app.domain_layer import validate_envelope
from app.knowledge.glossary import GlossaryStore
from app.policy import AmbiguityService
from app.understanding.agent import UnderstandingAgent


def test_wrong_domain_glossary_blocks_embed():
    und_agent = UnderstandingAgent()
    # eng meeting mentioning HR 校准 term from hr glossary
    _, res = und_agent.understand(
        meeting_id="m1",
        org_domains=["eng"],
        segments=["今天讨论校准结果和 HC 编制"],
    )
    assert res.wrong_domain_hits or "HC" in res.unknown_terms
    assert res.blocks_embed is True


def test_eng_domain_ok():
    _, res = UnderstandingAgent().understand(
        meeting_id="m2",
        org_domains=["eng"],
        segments=["发布灰度 canary 回滚准备好了，你补一下超时文档"],
    )
    assert res.quality == "ok"
    assert res.blocks_embed is False


def test_artifact_map_reduce_envelope_valid():
    agent = ArtifactAgent()
    env = agent.build_action_items_envelope(
        meeting_id="m3",
        org_domains=["eng"],
        scenario_type="tech_review",
        skill_pack_id="eng/R1_req_sync@0.1.0",
        segments=["你补齐超时和重试约定", "限流阈值是否统一？"],
    )
    assert validate_envelope(env) == []
    assert env["payload"]["items"]
    assert env["payload"]["open_questions"]


def test_ambiguity_unresolved_fails_evaluator():
    amb = AmbiguityService()
    amb.open(
        "mx",
        "灰度",
        [
            {"sense_id": "a", "org_domain": "eng", "gloss": "发布"},
            {"sense_id": "b", "org_domain": "business", "gloss": "客群"},
        ],
    )
    art = ArtifactAgent().build_action_items_envelope(
        meeting_id="mx",
        org_domains=["eng", "business"],
        scenario_type="cross_req_align",
        skill_pack_id="cross/X1_gray_ambiguity@0.1.0",
        segments=["灰度各方同意了"],
    )
    res = Evaluator().evaluate(
        artifact=art, ambiguity_open=True, prose_claims_all_agree=True
    )
    assert res.passed is False


def test_glossary_isolation_helper():
    g = GlossaryStore()
    assert g.isolation_violation("校准", ["eng"], "hr") is True
    assert g.isolation_violation("灰度", ["eng"], "eng") is False
