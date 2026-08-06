"""M4 R1 旗舰闭环集成测试。"""

from __future__ import annotations

from pathlib import Path

from app.api.bff import BffApp
from app.connectors.jira_simulator import JiraSimulator
from app.connectors.mock_saas import MockJiraConnector, MockWeComClient
from app.connectors.persistent_defect import PersistentDefectConnector
from app.events import DomainEventType
from app.knowledge import KnowledgePlane
from app.orchestrator import Orchestrator
from app.store.meetings import MeetingDraft

ROOT = Path(__file__).resolve().parents[2]


def test_webhook_closes_continuum_open_item(tmp_path: Path):
    kp = KnowledgePlane()
    bridge = kp.series_bridge
    bridge.write_open_item(
        series_id="series_wh",
        item_id="mtg_wh_open",
        title="待关闭阻塞项",
        source_meeting_id="mtg_wh",
        org_domain="eng",
        classification="internal",
        write_class="wide",
        acl_principals=["u_pm"],
    )
    app = BffApp(ROOT)
    app.knowledge = kp
    draft = MeetingDraft(
        meeting_id="mtg_wh",
        org_domains=["eng"],
        scenario_code="tech_review",
        purpose="webhook 测试",
        success_criteria="",
        created_by="u_pm",
        idempotency_key="idem_wh",
        series_id="series_wh",
        work_objects=[{"work_object_id": "wo_wh", "status": "open"}],
    )
    app.store.create(draft)
    wh = app.internal_connector_webhook(
        "svc_connector",
        {
            "meeting_id": "mtg_wh",
            "work_object_id": "wo_wh",
            "status": "resolved",
            "external_id": "BUG-0001",
        },
    )
    assert wh["continuum_closed"] is True
    opens = bridge.briefing_open_items("series_wh", user_id="u_pm", org_domains=["eng"])
    assert opens == []
    events = [e.event_type for e in app.events.events]
    assert DomainEventType.CONTINUUM_ITEM_CLOSED in events


def test_r1_flagship_loop_idempotent_and_briefing_clean(tmp_path: Path):
    series_id = "series_r1_test"
    meeting_a = "mtg_r1_test_a"
    item_id = f"{meeting_a}_open"

    orch = Orchestrator(ROOT, allow_draft_skills=True)
    out_a = orch.bind_and_run(
        scenario_code="tech_review",
        meeting_id=meeting_a,
        series_id=series_id,
        hitl_passed=True,
    )
    wo = out_a["pipeline"]["work_objects"][0]
    idem = wo["idempotency_key"]

    defect = PersistentDefectConnector(tmp_path / "defects.json")
    jira = MockJiraConnector(backend=defect, simulator=JiraSimulator(backend=defect))
    j1 = jira.execute({"title": "缺陷", "idempotency_key": idem})
    j2 = jira.execute({"title": "缺陷", "idempotency_key": idem})
    assert j1["external_id"] == j2["external_id"]

    wecom = MockWeComClient()
    msg = wecom.send_markdown(touser=["u_pm"], content="通知", meeting_id=meeting_a)
    assert msg["msgid"]

    bff = BffApp(ROOT)
    bff.knowledge = orch.knowledge
    bff.store.create(
        MeetingDraft(
            meeting_id=meeting_a,
            org_domains=["eng"],
            scenario_code="tech_review",
            purpose="A",
            success_criteria="",
            created_by="u_pm",
            idempotency_key=f"idem_{meeting_a}",
            series_id=series_id,
            work_objects=[dict(wo)],
        )
    )
    wh = bff.internal_connector_webhook(
        "svc_connector",
        {
            "meeting_id": meeting_a,
            "work_object_id": wo["work_object_id"],
            "status": "done",
            "external_id": wo["external_id"],
            "series_id": series_id,
            "item_id": item_id,
        },
    )
    assert wh["continuum_closed"]

    brief = orch.dialog.briefing(
        user_id="u_pm",
        org_domains=["eng"],
        query="阻塞",
        series_id=series_id,
    )
    assert all(i.get("item_id") != item_id for i in (brief.series_open_items or []))

    out_b = orch.bind_and_run(
        scenario_code="tech_review",
        meeting_id="mtg_r1_test_b",
        series_id=series_id,
        hitl_passed=True,
    )
    assert out_b["pipeline"]["terminal"] == "succeeded"
    brief_b = orch.dialog.briefing(
        user_id="u_pm",
        org_domains=["eng"],
        query="阻塞",
        series_id=series_id,
    )
    assert all(i.get("item_id") != item_id for i in (brief_b.series_open_items or []))
