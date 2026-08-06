"""PostgreSQL / Redis 持久化集成测试 — 无 DB 时 skip。"""

from __future__ import annotations

import os
import uuid

import pytest

from app.cache.redis_client import IdempotencyCache, InMemoryJsonCache, RedisCache
from app.config import InfrastructureSettings
from app.memory.journal_entry import JournalEntry
from app.memory.postgres_repository import PostgresJournalRepository
from app.memory.repository import JournalCorruptError
from app.persistence.postgres import apply_migrations, connect
from app.runtime.factory import build_journal_repository, build_meeting_store
from app.store.meetings import MeetingDraft
from app.store.postgres_meetings import PostgresMeetingStore


def _db_url() -> str | None:
    url = os.getenv("JIYAOJUN_DATABASE_URL", "").strip()
    return url or None


def _redis_url() -> str | None:
    url = os.getenv("JIYAOJUN_REDIS_URL", "").strip()
    return url or None


def _can_connect(database_url: str) -> bool:
    try:
        conn = connect(database_url)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture
def db_conn():
    url = _db_url()
    if not url or not _can_connect(url):
        pytest.skip("PostgreSQL 不可用或未配置 JIYAOJUN_DATABASE_URL")
    conn = connect(url)
    apply_migrations(conn)
    conn.commit()
    yield conn
    conn.close()


@pytest.mark.integration
def test_two_journal_repos_share_session(db_conn):
    """两个 repo 实例读写同一 session journal。"""
    session_id = f"int_sess_{uuid.uuid4().hex[:8]}"
    repo_a = PostgresJournalRepository(db_conn)
    repo_b = PostgresJournalRepository(db_conn)

    entry = JournalEntry(
        id=f"je_{uuid.uuid4().hex[:8]}",
        parent_id=None,
        entry_type="message",
        timestamp="2026-08-06T12:00:00+00:00",
        payload={"role": "user", "content": "集成测试"},
        session_id=session_id,
    )
    repo_a.append_entry(session_id, entry)
    db_conn.commit()

    loaded = repo_b.load(session_id)
    assert len(loaded) == 1
    assert loaded[0].id == entry.id
    assert loaded[0].payload["content"] == "集成测试"


@pytest.mark.integration
def test_journal_duplicate_entry_id_raises(db_conn):
    """重复 entry_id append 应抛 JournalCorruptError。"""
    session_id = f"int_dup_{uuid.uuid4().hex[:8]}"
    repo = PostgresJournalRepository(db_conn)
    eid = f"je_dup_{uuid.uuid4().hex[:8]}"
    entry = JournalEntry(
        id=eid,
        parent_id=None,
        entry_type="message",
        timestamp="2026-08-06T12:00:00+00:00",
        payload={"role": "user", "content": "first"},
        session_id=session_id,
    )
    repo.append_entry(session_id, entry)
    db_conn.commit()

    dup = JournalEntry(
        id=eid,
        parent_id=None,
        entry_type="message",
        timestamp="2026-08-06T12:01:00+00:00",
        payload={"role": "user", "content": "dup"},
        session_id=session_id,
    )
    with pytest.raises(JournalCorruptError):
        repo.append_entry(session_id, dup)


@pytest.mark.integration
def test_meeting_persist_hitl_and_work_links(db_conn):
    """meeting create/update 后新 store 实例仍可见 hitl_tasks 与 work_links。"""
    store_a = PostgresMeetingStore(db_conn)
    meeting_id = f"mtg_{uuid.uuid4().hex[:10]}"
    idem = f"idem_{uuid.uuid4().hex[:10]}"
    draft = MeetingDraft(
        meeting_id=meeting_id,
        org_domains=["eng"],
        scenario_code="tech_review",
        purpose="集成测试",
        success_criteria="持久化",
        created_by="user_int",
        idempotency_key=idem,
        hitl_tasks={"hitl_1": {"status": "pending", "reason": "approve"}},
        work_objects=[
            {
                "work_object_id": "wo_int_1",
                "idempotency_key": f"wo_idem_{uuid.uuid4().hex[:6]}",
                "connector_id": "connector.defect.create",
                "org_domain": "eng",
                "object_type": "defect",
                "production_effect": "draft_only",
                "meeting_id": meeting_id,
                "status": "open",
            }
        ],
    )
    created, is_new = store_a.create(draft)
    assert is_new
    db_conn.commit()

    created.hitl_tasks["hitl_1"]["status"] = "approved"
    created.work_objects[0]["status"] = "synced"
    store_a.update(created)
    db_conn.commit()

    store_b = PostgresMeetingStore(db_conn)
    loaded = store_b.get(meeting_id)
    assert loaded is not None
    assert loaded.hitl_tasks["hitl_1"]["status"] == "approved"
    assert loaded.work_objects[0]["status"] == "synced"

    link_rows = db_conn.execute(
        "SELECT work_object_id FROM app_work_link WHERE meeting_id = %s",
        (meeting_id,),
    ).fetchall()
    assert len(link_rows) == 1
    assert str(link_rows[0][0]) == "wo_int_1"


@pytest.mark.integration
def test_factory_builds_postgres_stores():
    url = _db_url()
    if not url or not _can_connect(url):
        pytest.skip("PostgreSQL 不可用")
    settings = InfrastructureSettings(
        storage_backend="postgres",
        database_url=url,
    )
    repo = build_journal_repository(settings)
    store = build_meeting_store(settings)
    assert isinstance(repo, PostgresJournalRepository)
    assert isinstance(store, PostgresMeetingStore)


@pytest.mark.integration
def test_redis_idempotency_set_nx():
    url = _redis_url()
    if not url:
        pytest.skip("JIYAOJUN_REDIS_URL 未配置")
    try:
        backend = RedisCache(url)
    except Exception:
        pytest.skip("Redis 不可用")

    cache = IdempotencyCache(backend)
    key = f"int_idem_{uuid.uuid4().hex[:8]}"
    assert cache.try_acquire(key) is True
    assert cache.try_acquire(key) is False
    cache.release(key)
    assert cache.try_acquire(key) is True


@pytest.mark.integration
def test_memory_idempotency_set_nx():
    """内存后端 set_nx 行为与 Redis 一致。"""
    cache = IdempotencyCache(InMemoryJsonCache())
    key = f"mem_idem_{uuid.uuid4().hex[:8]}"
    assert cache.try_acquire(key) is True
    assert cache.try_acquire(key) is False


@pytest.mark.integration
def test_task_projection_survives_restart(db_conn):
    """任务状态写入 app_task_projection 后，新 store 实例可读回。"""
    from app.persistence.task_projection import (
        PostgresTaskProjectionStore,
        TaskProjectionJournalHook,
    )

    session_id = f"int_task_{uuid.uuid4().hex[:8]}"
    task_id = f"task_{uuid.uuid4().hex[:8]}"
    store = PostgresTaskProjectionStore(db_conn)
    hook = TaskProjectionJournalHook(inner=None, store=store)
    hook.on_task_state(
        session_id,
        {
            "task_id": task_id,
            "status": "running",
            "owner_user_id": "u_int",
            "kind": "pipeline",
            "terminal": "",
        },
    )
    db_conn.commit()

    store_b = PostgresTaskProjectionStore(db_conn)
    loaded = store_b.get(task_id)
    assert loaded is not None
    assert loaded["status"] == "running"
    assert loaded["session_id"] == session_id
    assert loaded["owner_user_id"] == "u_int"
