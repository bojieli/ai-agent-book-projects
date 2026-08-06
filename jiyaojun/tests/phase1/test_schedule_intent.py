"""Phase 1: Intent / Schedule / HITL / idempotent meeting create."""

from __future__ import annotations

from pathlib import Path

from app.api.app import ApiApp
from app.intent.classifier import IntentClassifier
from app.schedule.service import CalendarDirectory, ScheduleService
from app.store.meetings import MeetingStore


ROOT = Path(__file__).resolve().parents[2]


def test_intent_eng_and_hr():
    clf = IntentClassifier()
    r1 = clf.classify("接口超时澄清一下")
    assert r1.scenario_code == "tech_review"
    assert r1.org_domains == ["eng"]
    hr = clf.classify("本季度绩效校准")
    assert hr.scenario_code == "perf_calibration"
    assert hr.org_domains == ["hr"]


def test_schedule_idempotent_no_duplicate(tmp_path: Path):
    store = MeetingStore(tmp_path / "m.json")
    cal = CalendarDirectory(ROOT / "fixtures" / "calendar")
    svc = ScheduleService(store, cal)
    a = svc.schedule_from_calendar(
        event_id="cal_eng_001",
        purpose="需求澄清超时",
        idempotency_key="idem-1",
        created_by="u_pm",
    )
    b = svc.schedule_from_calendar(
        event_id="cal_eng_001",
        purpose="需求澄清超时",
        idempotency_key="idem-1",
        created_by="u_pm",
    )
    assert a["created_new"] is True
    assert b["created_new"] is False
    assert a["meeting"].meeting_id == b["meeting"].meeting_id
    assert a["meeting"].org_domains == ["eng"]
    assert a["meeting"].scenario_code == "tech_review"


def test_hr_schedule_requires_hitl_and_critical():
    store = MeetingStore()
    cal = CalendarDirectory(ROOT / "fixtures" / "calendar")
    svc = ScheduleService(store, cal)
    out = svc.schedule_from_calendar(
        event_id="cal_hr_001",
        purpose="绩效校准",
        idempotency_key="idem-hr",
        created_by="u_hrbp",
    )
    assert out["needs_hitl"] is True
    assert out["meeting"].classification == "critical"
    assert out["meeting"].status == "pending_hitl"
    m = svc.resolve_hitl(out["meeting"].meeting_id, "schedule_confirm", "approve")
    assert m.status == "scheduled"


def test_api_post_meetings_replay(tmp_path: Path, monkeypatch):
    api = ApiApp(ROOT)
    api.store = MeetingStore(tmp_path / "meetings.json")
    from app.events import EventLog
    from app.schedule.service import ScheduleService

    api.schedule = ScheduleService(api.store, api.calendar, EventLog())
    body = {
        "event_id": "cal_eng_001",
        "purpose": "需求澄清",
        "idempotency_key": f"api-idem-{tmp_path.name}",
        "created_by": "u_pm",
    }
    r1 = api.post_meetings(body)
    r2 = api.post_meetings(body)
    assert r1["created_new"] is True
    assert r2["created_new"] is False
    assert r1["meeting_id"] == r2["meeting_id"]
    assert r1["org_domains"]
    assert r1["scenario_code"]
