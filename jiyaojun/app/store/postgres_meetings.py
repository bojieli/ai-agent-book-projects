"""PostgreSQL MeetingStore — 与内存版 API 对齐，含 work_link 同步。"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from typing import Any

import psycopg

from app.store.meetings import MeetingDraft


class PostgresMeetingStore:
    """PostgreSQL 会议草稿存储；create 幂等；update 同步 app_work_link。"""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def create(self, draft: MeetingDraft) -> tuple[MeetingDraft, bool]:
        with self._conn.transaction():
            row = self._conn.execute(
                "SELECT meeting_id, payload FROM app_meeting WHERE idempotency_key = %s",
                (draft.idempotency_key,),
            ).fetchone()
            if row:
                existing = _payload_to_draft(row[1], str(row[0]))
                return existing, False

            if not draft.meeting_id:
                draft.meeting_id = f"mtg_{uuid.uuid4().hex[:10]}"

            payload = json.dumps(asdict(draft), ensure_ascii=False)
            self._conn.execute(
                """
                INSERT INTO app_meeting (meeting_id, idempotency_key, payload)
                VALUES (%s, %s, %s::jsonb)
                """,
                (draft.meeting_id, draft.idempotency_key, payload),
            )
            self._upsert_work_links(draft)
            return draft, True

    def get(self, meeting_id: str) -> MeetingDraft | None:
        row = self._conn.execute(
            "SELECT meeting_id, payload FROM app_meeting WHERE meeting_id = %s",
            (meeting_id,),
        ).fetchone()
        if not row:
            return None
        return _payload_to_draft(row[1], str(row[0]))

    def update(self, meeting: MeetingDraft) -> MeetingDraft:
        with self._conn.transaction():
            payload = json.dumps(asdict(meeting), ensure_ascii=False)
            self._conn.execute(
                """
                UPDATE app_meeting
                SET payload = %s::jsonb, updated_at = now()
                WHERE meeting_id = %s
                """,
                (payload, meeting.meeting_id),
            )
            self._upsert_work_links(meeting)
            return meeting

    def list_all(self) -> list[MeetingDraft]:
        rows = self._conn.execute(
            "SELECT meeting_id, payload FROM app_meeting ORDER BY meeting_id"
        ).fetchall()
        return [_payload_to_draft(row[1], str(row[0])) for row in rows]

    def _upsert_work_links(self, meeting: MeetingDraft) -> None:
        """从 meeting.work_objects 同步 app_work_link（upsert）。"""
        for wo in meeting.work_objects or []:
            work_object_id = str(wo.get("work_object_id") or wo.get("id") or "")
            idem_key = str(wo.get("idempotency_key") or "")
            if not work_object_id or not idem_key:
                continue
            payload = json.dumps(wo, ensure_ascii=False)
            self._conn.execute(
                """
                INSERT INTO app_work_link
                  (meeting_id, work_object_id, idempotency_key, payload)
                VALUES (%s, %s, %s, %s::jsonb)
                ON CONFLICT (meeting_id, work_object_id) DO UPDATE
                  SET idempotency_key = EXCLUDED.idempotency_key,
                      payload = EXCLUDED.payload,
                      updated_at = now()
                """,
                (meeting.meeting_id, work_object_id, idem_key, payload),
            )


def _payload_to_draft(payload: Any, meeting_id: str) -> MeetingDraft:
    if isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = dict(payload or {})
    data["meeting_id"] = meeting_id
    return MeetingDraft(**data)
