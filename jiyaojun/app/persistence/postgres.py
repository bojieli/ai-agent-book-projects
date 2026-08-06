"""PostgreSQL 连接、事务与幂等迁移。"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator

import psycopg


def normalize_dsn(url: str) -> str:
    """将 SQLAlchemy 风格 DSN 规范化为 psycopg 可连接 URL（去掉 +psycopg）。"""
    if "+psycopg" in url:
        return url.replace("postgresql+psycopg://", "postgresql://", 1)
    return url


def connect(database_url: str, **kwargs: Any) -> psycopg.Connection:
    """建立 PostgreSQL 连接；连接失败时抛出明确异常，不静默吞掉。"""
    dsn = normalize_dsn(database_url)
    try:
        return psycopg.connect(dsn, **kwargs)
    except Exception as exc:
        raise ConnectionError(f"无法连接 PostgreSQL: {exc}") from exc


def get_migrations_dir() -> Path:
    """返回 migrations 目录（jiyaojun/migrations）。"""
    return Path(__file__).resolve().parents[2] / "migrations"


def _ensure_migration_table(conn: psycopg.Connection) -> None:
    """创建迁移版本表（若不存在）。"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS app_schema_migration (
          version    TEXT PRIMARY KEY,
          applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def _applied_versions(conn: psycopg.Connection) -> set[str]:
    """已应用的迁移版本集合。"""
    rows = conn.execute("SELECT version FROM app_schema_migration").fetchall()
    return {str(r[0]) for r in rows}


def _apply_one_migration(conn: psycopg.Connection, sql_path: Path) -> None:
    """执行单个 SQL 文件（跳过 BEGIN/COMMIT，按语句拆分）。"""
    raw = sql_path.read_text(encoding="utf-8")
    for stmt in _split_sql_statements(raw):
        conn.execute(stmt)


def _split_sql_statements(sql: str) -> list[str]:
    """将 SQL 文件拆为可执行语句（忽略注释与 BEGIN/COMMIT）。"""
    parts: list[str] = []
    current: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        upper = stripped.upper().rstrip(";")
        if upper in ("BEGIN", "COMMIT"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            parts.append("\n".join(current))
            current = []
    if current:
        parts.append("\n".join(current))
    return parts


def apply_migrations(conn: psycopg.Connection, migrations_dir: Path | None = None) -> list[str]:
    """
    幂等应用迁移：按文件名排序依次执行 001、002 等；
    已记录版本跳过；001 使用 IF NOT EXISTS 可安全重复。
    返回本次新应用的版本列表。
    """
    base = migrations_dir or get_migrations_dir()
    if not base.is_dir():
        raise FileNotFoundError(f"migrations 目录不存在: {base}")

    _ensure_migration_table(conn)
    applied = _applied_versions(conn)
    newly_applied: list[str] = []

    sql_files = sorted(base.glob("*.sql"))
    for sql_path in sql_files:
        version = sql_path.stem
        if version in applied:
            continue
        try:
            with conn.transaction():
                _apply_one_migration(conn, sql_path)
                conn.execute(
                    "INSERT INTO app_schema_migration (version, applied_at) VALUES (%s, %s)",
                    (version, datetime.now(timezone.utc)),
                )
            newly_applied.append(version)
        except Exception as exc:
            raise RuntimeError(f"迁移 {version} 失败: {exc}") from exc

    return newly_applied


@contextmanager
def transaction(conn: psycopg.Connection) -> Generator[psycopg.Connection, None, None]:
    """事务上下文：成功 commit，异常 rollback。"""
    try:
        with conn.transaction():
            yield conn
    except Exception:
        raise


def session_advisory_lock_key(session_id: str) -> int:
    """将 session_id 映射为 64 位 advisory lock 键（单事务内使用）。"""
    digest = hashlib.sha256(session_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=True)
