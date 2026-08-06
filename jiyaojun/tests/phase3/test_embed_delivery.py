"""Phase 3: persistent defect embed + delivery packs + sync."""

from __future__ import annotations

from pathlib import Path

from app.connectors.persistent_defect import PersistentDefectConnector
from app.connectors.work_embed import WorkEmbedService
from app.delivery.service import DeliveryService
from app.events import EventLog
from app.harness import ToolRuntime
from app.render import RenderService
from app.runtime.full import FullRuntime
from app.store.meetings import MeetingStore

ROOT = Path(__file__).resolve().parents[2]


def test_persistent_defect_idempotent(tmp_path: Path):
    conn = PersistentDefectConnector(tmp_path / "d.json")
    a = conn.execute({"title": "t1", "idempotency_key": "k1"})
    b = conn.execute({"title": "t1", "idempotency_key": "k1"})
    assert a["external_id"] == b["external_id"]
    conn.sync_status("k1", "open")
    assert conn.get("k1")["status"] == "open"


def test_work_embed_requires_hitl(tmp_path: Path):
    rt = ToolRuntime()
    rt.register(PersistentDefectConnector(tmp_path / "d2.json"))
    emb = WorkEmbedService(rt, EventLog())
    try:
        emb.embed_defect(
            meeting_id="m",
            title="x",
            org_domain="eng",
            artifact_id="a",
            production_effect_cap="draft_only",
            hitl_passed=False,
        )
        assert False, "should require hitl"
    except PermissionError:
        pass


def test_delivery_email_markdown_action_table():
    render = RenderService(ROOT / "app" / "render" / "default")
    d = DeliveryService(render, EventLog())
    arts = [
        {
            "artifact_kind": "action_items",
            "payload": {"items": [{"title": "补文档", "owner": "u_dev_a", "status": "committed"}]},
            "unresolved": [],
            "confidence": "med",
        }
    ]
    recs = d.deliver_pack(
        meeting_id="m_del",
        artifacts=arts,
        participants=["u_pm"],
        classification="internal",
        purpose="测试投递",
    )
    formats = {r.format for r in recs}
    assert formats == {"email_html", "markdown", "action_table"}
    assert all(not r.suppressed for r in recs)


def test_delivery_critical_suppressed():
    render = RenderService(ROOT / "app" / "render" / "default")
    d = DeliveryService(render, EventLog())
    recs = d.deliver_pack(
        meeting_id="m_crit",
        artifacts=[{"artifact_kind": "draft", "payload": {}, "unresolved": []}],
        participants=["u_hrbp"],
        classification="critical",
        purpose="高敏",
        allowlist=None,
    )
    assert all(r.suppressed for r in recs)


def test_e2e_phase3_lifecycle(tmp_path: Path):
    rt = FullRuntime(ROOT)
    rt.store = MeetingStore(tmp_path / "meetings.json")
    from app.schedule.service import ScheduleService

    rt.schedule = ScheduleService(rt.store, rt.calendar, rt.events)
    rt.defect = PersistentDefectConnector(tmp_path / "defects.json")
    rt.runtime.register(rt.defect)
    from app.connectors.work_embed import WorkEmbedService

    rt.work_embed = WorkEmbedService(rt.runtime, rt.events)
    out = rt.run_meeting_lifecycle(
        event_id="cal_eng_001",
        purpose="需求澄清接口超时",
        idempotency_key=f"e2e-{tmp_path.name}",
        user_id="u_pm",
        segments=["你补齐超时和重试约定", "限流是否统一？"],
        hitl_approve=True,
    )
    assert out["stage"] == "succeeded"
    assert out.get("transcript_chunks_indexed", 0) >= 1
    hits, _ = rt.knowledge.retrieve(
        user_id="u_pm",
        org_domains=out["org_domains"],
        query="超时重试",
        max_hops=3,
    )
    assert any(h.corpus == "transcript" for h in hits)
    assert out["work_object"]["object_type"] == "defect"
    assert out["defect_persisted"]["status"] == "open"
    assert out["deliveries"]
    assert "work_link.synced" in out["events"]
    assert "delivery.sent" in out["events"]
