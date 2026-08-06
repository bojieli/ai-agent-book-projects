"""Session journal + context compaction tests."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from app.memory.context import build_context
from app.memory.journal_entry import JournalEntry
from app.memory.repository import InMemoryJournalRepository, JsonlJournalRepository, JournalCorruptError
from app.memory.session_journal import SessionJournal
from app.memory.validation import JournalValidationError


def test_session_append_and_resume():
    repo = InMemoryJournalRepository()
    j1 = SessionJournal.resume("s1", repo)
    j1.append("message", {"role": "user", "content": "hello"})
    j1.append("message", {"role": "assistant", "content": "hi"})
    j2 = SessionJournal.resume("s1", repo)
    assert len(j2.entries) == 2
    assert j2.active_leaf_id == j2.entries[-1].id


def test_compaction_in_build_context():
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("s2", repo)
    for i in range(5):
        j.append("message", {"role": "user", "content": f"m{i}"})
    j.append_compaction(summary="前 5 条已压缩", covered_until_id=j.entries[0].id)
    j.append("message", {"role": "user", "content": "latest"})
    ctx = build_context(j, max_recent=10)
    assert ctx.compaction_summaries
    assert any("latest" in str(e) for e in ctx.recent_entries)


def test_append_compaction_if_needed_deterministic():
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("s2b", repo)
    for i in range(20):
        j.append("message", {"role": "user", "content": f"msg-{i}"})
    c1 = j.append_compaction_if_needed(max_uncompacted=8)
    assert c1 is not None
    assert "user:" in c1.payload["summary"]
    assert c1.payload["covered_until_id"]
    c2 = j.append_compaction_if_needed(max_uncompacted=8)
    assert c2 is None  # 未再次超过阈值不应重复 compact


def test_jsonl_atomic_and_corrupt_tail(tmp_path: Path):
    repo = JsonlJournalRepository(tmp_path / "journals")
    j = SessionJournal.resume("s3", repo)
    j.append("message", {"role": "user", "content": "ok"})
    j2 = SessionJournal.resume("s3", repo)
    assert len(j2.entries) == 1

    path = repo._path("s3")
    path.write_text(path.read_text() + "{bad json\n", encoding="utf-8")
    with pytest.raises(JournalCorruptError):
        repo.load("s3")


def test_jsonl_invalid_entry_type(tmp_path: Path):
    repo = JsonlJournalRepository(tmp_path / "journals")
    path = repo._path("s4")
    path.write_text(
        json.dumps(
            {
                "id": "je_bad",
                "parent_id": None,
                "entry_type": "evil",
                "timestamp": "t",
                "payload": {},
                "session_id": "s4",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(JournalCorruptError):
        repo.load("s4")


def test_fork_from_persists_branch_marker():
    """branch marker 自身为 active leaf；fork 后追加消息走新分支。"""
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("s4", repo)
    e1 = j.append("message", {"role": "user", "content": "人工确认"})
    j.append("message", {"role": "assistant", "content": "wait"})
    branch = j.fork_from(e1.id)
    j2 = SessionJournal.resume("s4", repo)
    assert j2.active_leaf_id == branch.id
    j2.append("message", {"role": "user", "content": "branch msg"})
    ctx = build_context(j2)
    assert ctx.path_length == 2  # e1 + branch msg（不含 branch marker 与旧分叉）


def test_fork_resume_cross_repo_excludes_old_branch(tmp_path: Path):
    """跨 service/repo resume：JSONL 持久化后新实例保留新分支、排除旧分叉。"""
    journal_dir = tmp_path / "journals"
    repo = JsonlJournalRepository(journal_dir)
    j = SessionJournal.resume("s_cross", repo)
    root = j.append("message", {"role": "user", "content": "root"})
    j.append("message", {"role": "assistant", "content": "old branch tail"})
    j.fork_from(root.id)
    j.append("message", {"role": "user", "content": "new branch only"})

    repo2 = JsonlJournalRepository(journal_dir)
    j2 = SessionJournal.resume("s_cross", repo2)
    ctx = build_context(j2)
    assert "new branch only" in str(ctx.recent_entries)
    assert "old branch tail" not in str(ctx.recent_entries)


def test_forward_parent_illegal():
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("s_fwd", repo)
    j.append("message", {"role": "user", "content": "a"}, entry_id="a1")
    with pytest.raises(JournalValidationError, match="forward parent"):
        repo.append_entry(
            "s_fwd",
            JournalEntry(
                id="b1",
                parent_id="future",
                entry_type="message",
                timestamp="t",
                payload={},
                session_id="s_fwd",
            ),
        )


def test_concurrent_append_memory_no_loss():
    """同 session 50 并发 append — 内存仓库不丢条目。"""
    repo = InMemoryJournalRepository()
    barrier = threading.Barrier(50)

    def worker(i: int) -> None:
        barrier.wait()
        j = SessionJournal.resume("s_conc", repo)
        j.append("message", {"role": "user", "content": f"m{i}"})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    entries = repo.load("s_conc")
    assert len(entries) == 50


def test_concurrent_append_jsonl_no_loss(tmp_path: Path):
    """同 session 50 并发 append — JSONL 单进程锁不丢条目。"""
    repo = JsonlJournalRepository(tmp_path / "j")
    barrier = threading.Barrier(50)

    def worker(i: int) -> None:
        barrier.wait()
        j = SessionJournal.resume("s_jcon", repo)
        j.append("message", {"role": "user", "content": f"j{i}"})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    entries = repo.load("s_jcon")
    assert len(entries) == 50


def test_validation_duplicate_id():
    repo = InMemoryJournalRepository()
    j = SessionJournal.resume("s5", repo)
    j.append("message", {"role": "user", "content": "a"}, entry_id="dup")
    with pytest.raises(JournalCorruptError):
        j.append("message", {"role": "user", "content": "b"}, entry_id="dup")
