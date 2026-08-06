"""End-to-end feature coverage for remaining architecture surfaces (all mocked)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.agents.hallucination import detect_hallucination
from app.api.bff import BffApp
from app.connectors.mcp_server import MockMcpServer
from app.connectors.mock import MockDefectConnector
from app.connectors.departments import department_connectors
from app.eval.negative_runners import run_negative_catalog
from app.harness import ToolRuntime
from app.knowledge.series import MeetingSeriesStore, SeriesOpenItem
from app.ops.capacity import CapacityPolicy, allow_agentic_retrieve, allow_reindex, is_night
from app.planes.dialog.voice_stub import VoiceInterfaceStub
from app.planes.pipeline.sop_runner import SopPipelineRunner
from app.render.charts import invent_chart_forbidden, render_charts
from app.security.authz import MockAuthZ

ROOT = Path(__file__).resolve().parents[2]


def test_bff_chat_sse_and_admin_and_internal(tmp_path: Path):
    app = BffApp(ROOT)
    app.store = __import__("app.store.meetings", fromlist=["MeetingStore"]).MeetingStore(
        tmp_path / "m.json"
    )
    from app.schedule.service import ScheduleService
    from app.events import EventLog

    app.schedule = ScheduleService(app.store, app.calendar, EventLog())
    app.events = EventLog()

    chunks = list(app.post_chat_completions("u_pm", {"messages": [{"content": "帮我订需求澄清会"}]}))
    assert any("[DONE]" in c for c in chunks)

    created = app.post_meetings(
        {
            "event_id": "cal_eng_001",
            "purpose": "需求澄清",
            "idempotency_key": f"bff-{tmp_path.name}",
            "created_by": "u_pm",
        }
    )
    mid = created["meeting_id"]
    if created["needs_hitl"]:
        app.post_hitl(mid, "schedule_confirm", {"decision": "approve"})
    app.patch_meeting("u_pm", mid, {"purpose": "更新后的目的"})
    m = app.get_meeting(mid)
    assert m["purpose"] == "更新后的目的"

    # store an artifact for render
    mobj = app.store.get(mid)
    mobj.artifacts = [
        {
            "artifact_kind": "metrics",
            "payload": {},
            "chart_series": [
                {
                    "series_id": "s1",
                    "label": "x",
                    "points": [{"x": 1, "y": 2}],
                }
            ],
            "unresolved": [],
        }
    ]
    app.store.update(mobj)
    rendered = app.post_render("u_pm", mid, {})
    assert rendered["status"] == "completed"
    assert rendered["charts"][0]["status"] == "ok"

    assert app.admin_skills_list("u_admin")
    app.admin_skills_submit("u_admin", "eng/R1_req_sync@0.1.0")
    app.admin_skills_approve("u_admin", "eng/R1_req_sync@0.1.0", "er1")
    assert app.skill_admin.production_loadable("eng/R1_req_sync@0.1.0")

    g = app.admin_glossary_approve("u_admin", "eng", "半成功", "部分成功需补偿")
    assert g["status"] == "approved"
    q = app.admin_quotas_put("u_admin", {"max_embed_attempts": 2})
    assert q["max_embed_attempts"] == 2
    assert app.admin_usage_get("u_admin")

    tr = app.internal_transcripts(
        "svc_transcript",
        {
            "meeting_id": mid,
            "transcript_document_id": "td1",
            "object_key": "s3://x",
            "segments": [
                {"speaker": "PM", "text": "今天讨论限流阈值与网关统一", "section": "议题"},
                {"speaker": "DEV", "text": "超时重试按规范 3 秒两次", "section": "决议"},
            ],
        },
        signature="mock-sign",
    )
    assert tr["ok"]
    assert tr["chunks_indexed"] >= 1
    hits, _ = app.knowledge.retrieve(
        user_id="u_pm",
        org_domains=m["org_domains"],
        query="限流阈值",
        max_hops=3,
    )
    assert any(h.corpus == "transcript" for h in hits)
    # seed work object for webhook
    mobj = app.store.get(mid)
    mobj.work_objects = [{"work_object_id": "wo1", "status": "draft"}]
    app.store.update(mobj)
    wh = app.internal_connector_webhook(
        "svc_connector",
        {"meeting_id": mid, "work_object_id": "wo1", "status": "open", "external_id": "BUG-9"},
    )
    assert wh["ok"]
    assert app.store.get(mid).work_objects[0]["status"] == "open"

    # non-admin denied
    try:
        app.admin_quotas_get("u_pm")
        assert False
    except PermissionError:
        pass


def test_sop_runner_r4_walls():
    runner = SopPipelineRunner(ROOT / "app/skills/eng/R4_release_review")
    ok = runner.run(checklist_ok=True, evaluate_ok=True, hitl_passed=True)
    assert ok.terminal == "succeeded"
    bad = runner.run(checklist_ok=False)
    assert bad.terminal == "failed"
    try:
        runner.run(skip_walls=True)
        assert False
    except ValueError:
        pass


def test_charts_and_hallucination_and_capacity():
    charts = render_charts([{"chart_series": None}])
    assert charts[0]["status"] == "data_insufficient"
    try:
        invent_chart_forbidden([1, 2, 3])
        assert False
    except ValueError:
        pass
    h = detect_hallucination(
        artifact_payload={"summary": "转化率100%"},
        source_quotes=["大概四成"],
    )
    assert h.flagged
    night = datetime(2026, 8, 3, 1, 0)
    assert is_night(night)
    assert allow_reindex(night) is False
    assert allow_agentic_retrieve(night, 0.2) is True
    assert allow_agentic_retrieve(night, 0.5) is False


def test_mcp_series_voice_negatives():
    rt = ToolRuntime()
    rt.register(MockDefectConnector())
    for c in department_connectors()[:2]:
        rt.register(c)
    mcp = MockMcpServer(rt)
    assert mcp.tools_list()
    out = mcp.tools_call(
        "connector.defect.create",
        {"title": "x", "idempotency_key": "mcp1"},
        meeting_id="m",
    )
    assert out["external_id"]

    series = MeetingSeriesStore()
    series.add_open(
        "s1",
        SeriesOpenItem(
            "i1",
            "阻塞网关",
            source_meeting_id="m0",
            org_domain="eng",
            acl_principals=["u_pm"],
        ),
    )
    assert series.briefing_payload("s1", user_id="u_pm", org_domains=["eng"])["open_count"] == 1
    series.close("s1", "i1")
    assert series.list_open("s1") == []

    voice = VoiceInterfaceStub()
    assert voice.reserve("m").status.startswith("reserved")
    try:
        voice.start_duplex("m")
        assert False
    except NotImplementedError:
        pass

    negs = run_negative_catalog()
    assert negs and all(ok for _, ok, _ in negs), negs


def test_authz_critical_artifact():
    az = MockAuthZ()
    hr = az.authenticate("u_hrbp")
    az.authorize(hr, "read", "artifact:critical")
    pm = az.authenticate("u_pm")
    try:
        az.authorize(pm, "read", "artifact:critical")
        assert False
    except PermissionError:
        pass
