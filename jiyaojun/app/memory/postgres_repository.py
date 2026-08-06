"""PostgreSQL Session Journal 仓库 — 实现 JournalRepository Protocol。"""

from __future__ import annotations

import json
from typing import Any

import psycopg

from app.memory.journal_entry import JournalEntry
from app.memory.repository import JournalCorruptError
from app.memory.validation import validate_journal_entries
from app.persistence.postgres import session_advisory_lock_key


class PostgresJournalRepository:
    """PostgreSQL append-only journal；同 session 事务 + advisory lock 防并发重复。"""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def list_sessions(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT session_id FROM app_session_journal_entry ORDER BY session_id"
        ).fetchall()
        return [str(r[0]) for r in rows]

    def load(self, session_id: str) -> list[JournalEntry]:
        rows = self._conn.execute(
            """
            SELECT entry_id, entry_type, parent_id, ts, payload, session_id
            FROM app_session_journal_entry
            WHERE session_id = %s
            ORDER BY seq
            """,
            (session_id,),
        ).fetchall()
        entries = [_row_to_entry(session_id, row) for row in rows]
        validate_journal_entries(session_id, entries)
        return entries

    def append_entry(self, session_id: str, entry: JournalEntry) -> None:
        with self._conn.transaction():
            lock_key = session_advisory_lock_key(session_id)
            self._conn.execute("SELECT pg_advisory_xact_lock(%s)", (lock_key,))

            dup = self._conn.execute(
                """
                SELECT 1 FROM app_session_journal_entry
                WHERE session_id = %s AND entry_id = %s
                """,
                (session_id, entry.id),
            ).fetchone()
            if dup:
                raise JournalCorruptError(f"duplicate append id {entry.id}")

            existing = self.load(session_id)
            trial = existing + [entry]
            validate_journal_entries(session_id, trial)

            self._conn.execute(
                """
                INSERT INTO app_session_journal_entry
                  (session_id, entry_id, entry_type, parent_id, ts, payload)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    session_id,
                    entry.id,
                    entry.entry_type,
                    entry.parent_id,
                    entry.timestamp,
                    json.dumps(entry.payload, ensure_ascii=False),
                ),
            )


def _row_to_entry(session_id: str, row: tuple[Any, ...]) -> JournalEntry:
    entry_id, entry_type, parent_id, ts, payload, row_session_id = row
    if isinstance(payload, str):
        payload_data = json.loads(payload)
    else:
        payload_data = payload or {}
    sid = str(row_session_id or session_id)
    return JournalEntry(
        id=str(entry_id),
        parent_id=parent_id,
        entry_type=str(entry_type),
        timestamp=str(ts),
        payload=payload_data,
        session_id=sid,
    )
