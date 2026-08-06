"""Schedule + calendar/contacts adapters (Phase 1 — real interface, file fixtures)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.domain_layer.registry import load_or_default
from app.events import DomainEvent, DomainEventType, EventLog
from app.intent.classifier import IntentClassifier
from app.store.meetings import MeetingDraft, MeetingStore


@dataclass
class CalendarEvent:
    event_id: str
    title: str
    organizer: str
    attendees: list[str]
    start: str
    end: str


@dataclass
class Contact:
    user_id: str
    name: str
    org_domain: str
    email: str


class CalendarDirectory:
    """Loads from fixtures — swap implementation for real Graph/Exchange later."""

    def __init__(self, fixture_dir: Path) -> None:
        self.fixture_dir = fixture_dir
        cal = json.loads((fixture_dir / "calendar.json").read_text(encoding="utf-8"))
        contacts = json.loads((fixture_dir / "contacts.json").read_text(encoding="utf-8"))
        self.events = [CalendarEvent(**e) for e in cal["events"]]
        self.contacts = {c["user_id"]: Contact(**c) for c in contacts["contacts"]}

    def get_event(self, event_id: str) -> CalendarEvent | None:
        return next((e for e in self.events if e.event_id == event_id), None)

    def get_contact(self, user_id: str) -> Contact | None:
        return self.contacts.get(user_id)


class ScheduleService:
    def __init__(
        self,
        store: MeetingStore,
        calendar: CalendarDirectory,
        events: EventLog | None = None,
    ) -> None:
        self.store = store
        self.calendar = calendar
        self.intent = IntentClassifier()
        self.registry = load_or_default()
        self.events = events or EventLog()

    def schedule_from_calendar(
        self,
        *,
        event_id: str,
        purpose: str,
        idempotency_key: str,
        created_by: str,
        require_hitl_if_hr: bool = True,
    ) -> dict[str, Any]:
        ev = self.calendar.get_event(event_id)
        if not ev:
            raise KeyError(f"calendar event not found: {event_id}")
        intent = self.intent.classify(purpose, ev.title)
        scenario = self.registry.get_scenario(intent.scenario_code)

        classification = scenario.classification
        # HR default high-sensitive
        if "hr" in intent.org_domains and classification not in {"critical", "confidential"}:
            classification = "critical"

        needs_hitl = require_hitl_if_hr and (
            "hr" in intent.org_domains or scenario.default_embed_gate in {"block", "confirm_only"}
        )

        draft = MeetingDraft(
            meeting_id="",
            org_domains=intent.org_domains,
            scenario_code=intent.scenario_code,
            purpose=purpose or ev.title,
            success_criteria=f"scenario={intent.scenario_code}",
            created_by=created_by,
            idempotency_key=idempotency_key,
            classification=classification,
            participants=list(ev.attendees),
            skill_pack_id=f"{scenario.skill_relpath}@0.1.0",
            status="pending_hitl" if needs_hitl else "scheduled",
        )
        if needs_hitl:
            draft.hitl_tasks["schedule_confirm"] = {
                "kind": "schedule_confirm",
                "status": "open",
                "payload": {"event_id": event_id, "scenario": intent.scenario_code},
            }

        meeting, created = self.store.create(draft)
        if created:
            self.events.emit(
                DomainEvent(
                    DomainEventType.MEETING_SCHEDULED,
                    meeting.meeting_id,
                    {
                        "series_id": meeting.series_id,
                        "org_domains": meeting.org_domains,
                        "skill_pack_ids": [meeting.skill_pack_id],
                        "event_id": event_id,
                        "created_new": True,
                    },
                    producer="schedule",
                )
            )
            if needs_hitl:
                self.events.emit(
                    DomainEvent(
                        DomainEventType.HITL_REQUESTED,
                        meeting.meeting_id,
                        {"task_id": "schedule_confirm", "kind": "schedule_confirm"},
                        producer="schedule",
                    )
                )
        return {
            "meeting": meeting,
            "created_new": created,
            "intent": intent,
            "needs_hitl": needs_hitl and created,
        }

    def resolve_hitl(
        self,
        meeting_id: str,
        task_id: str,
        decision: str,
        patch: dict[str, Any] | None = None,
    ) -> MeetingDraft:
        m = self.store.get(meeting_id)
        if not m:
            raise KeyError(meeting_id)
        task = m.hitl_tasks.get(task_id)
        if not task:
            raise KeyError(task_id)
        task["status"] = "resolved"
        task["decision"] = decision
        if patch:
            if "purpose" in patch:
                m.purpose = patch["purpose"]
            if "scenario_code" in patch:
                m.scenario_code = patch["scenario_code"]
                sc = self.registry.get_scenario(m.scenario_code)
                m.skill_pack_id = f"{sc.skill_relpath}@0.1.0"
                m.org_domains = [sc.org_domain] if sc.story_id != "X1" else ["eng", "business"]
        if decision == "approve" and task_id == "schedule_confirm":
            m.status = "scheduled"
        self.events.emit(
            DomainEvent(
                DomainEventType.HITL_RESOLVED,
                meeting_id,
                {"task_id": task_id, "decision": decision, "patch": patch},
                producer="schedule",
            )
        )
        return self.store.update(m)
