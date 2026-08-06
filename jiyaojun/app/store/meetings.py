"""In-memory + file-backed meeting store (idempotent create)."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MeetingDraft:
    meeting_id: str
    org_domains: list[str]
    scenario_code: str
    purpose: str
    success_criteria: str
    created_by: str
    idempotency_key: str
    classification: str = "internal"
    status: str = "draft"
    series_id: str | None = None
    project_id: str | None = None
    skill_pack_id: str | None = None
    participants: list[str] = field(default_factory=list)
    hitl_tasks: dict[str, dict[str, Any]] = field(default_factory=dict)
    pipeline_terminal: str | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    work_objects: list[dict[str, Any]] = field(default_factory=list)
    deliveries: list[dict[str, Any]] = field(default_factory=list)
    transcript_document_id: str | None = None
    transcript_object_key: str | None = None


class MeetingStore:
    def __init__(self, persist_path: Path | None = None) -> None:
        self._lock = threading.Lock()
        self._by_id: dict[str, MeetingDraft] = {}
        self._by_idem: dict[str, str] = {}
        self._path = persist_path
        if persist_path and persist_path.exists():
            self._load()

    def _load(self) -> None:
        assert self._path
        data = json.loads(self._path.read_text(encoding="utf-8"))
        for row in data.get("meetings", []):
            m = MeetingDraft(**row)
            self._by_id[m.meeting_id] = m
            self._by_idem[m.idempotency_key] = m.meeting_id

    def _save(self) -> None:
        if not self._path:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"meetings": [asdict(m) for m in self._by_id.values()]}
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def create(self, draft: MeetingDraft) -> tuple[MeetingDraft, bool]:
        """Returns (meeting, created_new). Replay with same idempotency_key does not duplicate."""
        with self._lock:
            if draft.idempotency_key in self._by_idem:
                existing = self._by_id[self._by_idem[draft.idempotency_key]]
                return existing, False
            if not draft.meeting_id:
                draft.meeting_id = f"mtg_{uuid.uuid4().hex[:10]}"
            self._by_id[draft.meeting_id] = draft
            self._by_idem[draft.idempotency_key] = draft.meeting_id
            self._save()
            return draft, True

    def get(self, meeting_id: str) -> MeetingDraft | None:
        return self._by_id.get(meeting_id)

    def update(self, meeting: MeetingDraft) -> MeetingDraft:
        with self._lock:
            self._by_id[meeting.meeting_id] = meeting
            self._save()
            return meeting

    def list_all(self) -> list[MeetingDraft]:
        return list(self._by_id.values())
