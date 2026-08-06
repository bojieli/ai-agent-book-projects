"""任务投影持久化 — 将 scheduler 状态镜像到 PostgreSQL。"""

from __future__ import annotations

import json
from typing import Any

import psycopg


class PostgresTaskProjectionStore:
    """app_task_projection 的读写封装。"""

    def __init__(self, conn: psycopg.Connection) -> None:
        self._conn = conn

    def upsert(
        self,
        *,
        task_id: str,
        session_id: str,
        owner_user_id: str,
        status: str,
        kind: str = "pipeline",
        payload: dict[str, Any] | None = None,
    ) -> None:
        """按 task_id 幂等写入最新状态。"""
        body = json.dumps(payload or {}, ensure_ascii=False)
        with self._conn.transaction():
            self._conn.execute(
                """
                INSERT INTO app_task_projection
                  (task_id, session_id, owner_user_id, status, kind, payload)
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (task_id) DO UPDATE
                  SET session_id = EXCLUDED.session_id,
                      owner_user_id = EXCLUDED.owner_user_id,
                      status = EXCLUDED.status,
                      kind = EXCLUDED.kind,
                      payload = EXCLUDED.payload,
                      updated_at = now()
                """,
                (task_id, session_id, owner_user_id, status, kind, body),
            )

    def get(self, task_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            """
            SELECT task_id, session_id, owner_user_id, status, kind, payload
            FROM app_task_projection
            WHERE task_id = %s
            """,
            (task_id,),
        ).fetchone()
        if not row:
            return None
        payload = row[5]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return {
            "task_id": str(row[0]),
            "session_id": str(row[1]),
            "owner_user_id": str(row[2]),
            "status": str(row[3]),
            "kind": str(row[4]),
            "payload": payload or {},
        }

    def list_by_session(self, session_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT task_id, session_id, owner_user_id, status, kind, payload
            FROM app_task_projection
            WHERE session_id = %s
            ORDER BY updated_at
            """,
            (session_id,),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            payload = row[5]
            if isinstance(payload, str):
                payload = json.loads(payload)
            out.append(
                {
                    "task_id": str(row[0]),
                    "session_id": str(row[1]),
                    "owner_user_id": str(row[2]),
                    "status": str(row[3]),
                    "kind": str(row[4]),
                    "payload": payload or {},
                }
            )
        return out


class TaskProjectionJournalHook:
    """在 journal 任务状态回调之外，同步写入 PostgreSQL 投影。"""

    def __init__(
        self,
        inner: Any,
        store: PostgresTaskProjectionStore,
        *,
        default_kind: str = "pipeline",
    ) -> None:
        self._inner = inner
        self._store = store
        self._default_kind = default_kind

    def on_task_state(self, session_id: str, payload: dict[str, Any]) -> None:
        if self._inner is not None:
            self._inner.on_task_state(session_id, payload)
        task_id = str(payload.get("task_id") or "")
        status = str(payload.get("status") or "")
        if not task_id or not status:
            return
        self._store.upsert(
            task_id=task_id,
            session_id=session_id,
            owner_user_id=str(payload.get("owner_user_id") or ""),
            status=status,
            kind=str(payload.get("kind") or self._default_kind),
            payload=dict(payload),
        )
