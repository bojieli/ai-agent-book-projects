"""HTTP-ish API handlers (05 §4) — in-process for tests; ASGI later."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.schedule.service import CalendarDirectory, ScheduleService
from app.store.meetings import MeetingStore


class ApiApp:
    def __init__(self, root: Path) -> None:
        self.root = root
        data = root / "data" / "meetings.json"
        self.store = MeetingStore(data)
        self.calendar = CalendarDirectory(root / "fixtures" / "calendar")
        self.schedule = ScheduleService(self.store, self.calendar)

    def post_meetings(self, body: dict[str, Any]) -> dict[str, Any]:
        result = self.schedule.schedule_from_calendar(
            event_id=body["event_id"],
            purpose=body.get("purpose", ""),
            idempotency_key=body["idempotency_key"],
            created_by=body.get("created_by", "system"),
        )
        m = result["meeting"]
        return {
            "meeting_id": m.meeting_id,
            "created_new": result["created_new"],
            "org_domains": m.org_domains,
            "scenario_code": m.scenario_code,
            "status": m.status,
            "needs_hitl": result["needs_hitl"],
        }

    def get_meeting(self, meeting_id: str) -> dict[str, Any]:
        m = self.store.get(meeting_id)
        if not m:
            raise KeyError(meeting_id)
        return asdict(m)

    def post_hitl(self, meeting_id: str, task_id: str, body: dict[str, Any]) -> dict[str, Any]:
        m = self.schedule.resolve_hitl(
            meeting_id, task_id, body["decision"], body.get("patch")
        )
        return {"meeting_id": m.meeting_id, "status": m.status, "hitl_tasks": m.hitl_tasks}

    def get_pipeline(self, meeting_id: str) -> dict[str, Any]:
        m = self.store.get(meeting_id)
        if not m:
            raise KeyError(meeting_id)
        return {
            "meeting_id": meeting_id,
            "terminal": m.pipeline_terminal,
            "status": m.status,
            "work_objects": m.work_objects,
        }

    def get_artifacts(self, meeting_id: str, viewer: str) -> list[dict[str, Any]]:
        m = self.store.get(meeting_id)
        if not m:
            raise KeyError(meeting_id)
        # ACL: critical only allowlist participants for now
        if m.classification == "critical" and viewer not in m.participants:
            return []
        return list(m.artifacts)

    def get_deliveries(self, meeting_id: str) -> list[dict[str, Any]]:
        m = self.store.get(meeting_id)
        if not m:
            raise KeyError(meeting_id)
        return list(m.deliveries)
