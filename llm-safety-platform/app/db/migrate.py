"""Idempotent schema upgrades for existing databases (Postgres + SQLite)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.observability.chain_verify import GENESIS, compute_chain_hash


def _sqlite_has_column(engine: Engine, table: str, column: str) -> bool:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    return any(r[1] == column for r in rows)


def _pg_has_column(engine: Engine, table: str, column: str) -> bool:
    insp = inspect(engine)
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade_audit_chain_columns(engine: Engine) -> list[str]:
    """Add ``chain_hash`` / ``prev_chain_hash`` if missing (legacy DBs)."""
    applied: list[str] = []
    is_sqlite = engine.dialect.name == "sqlite"
    has_col = _sqlite_has_column if is_sqlite else _pg_has_column

    with engine.begin() as conn:
        if not has_col(engine, "audit_decisions", "chain_hash"):
            if is_sqlite:
                conn.execute(text("ALTER TABLE audit_decisions ADD COLUMN chain_hash VARCHAR(128) DEFAULT ''"))
            else:
                conn.execute(
                    text("ALTER TABLE audit_decisions ADD COLUMN IF NOT EXISTS chain_hash VARCHAR(128) DEFAULT ''")
                )
            applied.append("audit_decisions.chain_hash")

        if not has_col(engine, "audit_decisions", "prev_chain_hash"):
            if is_sqlite:
                conn.execute(
                    text("ALTER TABLE audit_decisions ADD COLUMN prev_chain_hash VARCHAR(128) DEFAULT ''")
                )
            else:
                conn.execute(
                    text(
                        "ALTER TABLE audit_decisions ADD COLUMN IF NOT EXISTS prev_chain_hash VARCHAR(128) DEFAULT ''"
                    )
                )
            applied.append("audit_decisions.prev_chain_hash")

    return applied


def backfill_audit_chain_hashes(engine: Engine) -> dict[str, Any]:
    """幂等回填 legacy 行的 ``chain_hash`` / ``prev_chain_hash`` 列。

    1. 列已有 hash → 跳过（保持幂等）
    2. ``body_json`` 含链字段 → 复制到列
    3. 其余按 ``id`` 升序顺序重算链（旧库无链字段时的 append 序）

    **边界**：多进程并发回填可能分叉链；生产须 **single-writer** 或 Postgres
    ``pg_advisory_lock`` 包裹本函数 + 后续写入（本仓未实现分布式锁）。
  """
    stats: dict[str, int] = {"skipped": 0, "copied_from_body": 0, "computed": 0}

    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT id, body_json, chain_hash, prev_chain_hash "
                "FROM audit_decisions ORDER BY id ASC"
            )
        ).fetchall()

        prev = GENESIS
        for row_id, body_json, col_hash, col_prev in rows:
            stored_hash = (col_hash or "").strip()
            if stored_hash:
                stats["skipped"] += 1
                prev = stored_hash
                continue

            try:
                sd = json.loads(body_json or "{}")
            except (json.JSONDecodeError, TypeError):
                sd = {}

            body_hash = (sd.get("chain_hash") or "").strip()
            if body_hash:
                new_hash = body_hash
                new_prev = (sd.get("prev_chain_hash") or GENESIS).strip() or GENESIS
                stats["copied_from_body"] += 1
                new_body = body_json
            else:
                new_prev = prev
                new_hash = compute_chain_hash(prev, sd)
                sd["prev_chain_hash"] = new_prev
                sd["chain_hash"] = new_hash
                new_body = json.dumps(sd, ensure_ascii=False)
                stats["computed"] += 1

            conn.execute(
                text(
                    "UPDATE audit_decisions "
                    "SET chain_hash = :h, prev_chain_hash = :p, body_json = :b "
                    "WHERE id = :id"
                ),
                {"h": new_hash, "p": new_prev, "b": new_body, "id": row_id},
            )
            prev = new_hash

    return stats


def upgrade_audit_chain(engine: Engine) -> dict[str, Any]:
    """Schema + data 幂等升级（启动时调用）。"""
    cols = upgrade_audit_chain_columns(engine)
    backfill = backfill_audit_chain_hashes(engine)
    return {"columns": cols, "backfill": backfill}
