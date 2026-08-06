"""Journal repositories — 原子 append + per-session 锁（同进程）。"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from app.memory.journal_entry import JournalEntry
from app.memory.validation import VALID_ENTRY_TYPES, validate_journal_entries

_lock_registry: dict[str, threading.RLock] = {}
_registry_guard = threading.Lock()


def _session_lock(key: str) -> threading.RLock:
    with _registry_guard:
        if key not in _lock_registry:
            _lock_registry[key] = threading.RLock()
        return _lock_registry[key]


class JournalCorruptError(ValueError):
    """JSONL 损坏或 schema 非法 — fail closed。"""


def _validate_entry_dict(session_id: str, data: dict[str, Any], line_no: int) -> JournalEntry:
    required = {"id", "entry_type", "timestamp"}
    missing = required - set(data.keys())
    if missing:
        raise JournalCorruptError(f"line {line_no}: missing fields {missing}")
    et = data["entry_type"]
    if et not in VALID_ENTRY_TYPES:
        raise JournalCorruptError(f"line {line_no}: invalid entry_type {et}")
    if data.get("session_id") and data["session_id"] != session_id:
        raise JournalCorruptError(f"line {line_no}: cross-session entry")
    return JournalEntry.from_dict(data)


class InMemoryJournalRepository:
    """内存仓库 — 单进程 per-session RLock + append-only。"""

    def __init__(self) -> None:
        self._store: dict[str, list[JournalEntry]] = {}
        self._revision: dict[str, int] = {}

    def list_sessions(self) -> list[str]:
        with _registry_guard:
            return list(self._store.keys())

    def load(self, session_id: str) -> list[JournalEntry]:
        with _session_lock(f"mem:{session_id}"):
            entries = list(self._store.get(session_id, []))
        validate_journal_entries(session_id, entries)
        return entries

    def append_entry(self, session_id: str, entry: JournalEntry) -> None:
        with _session_lock(f"mem:{session_id}"):
            entries = list(self._store.get(session_id, []))
            if any(e.id == entry.id for e in entries):
                raise JournalCorruptError(f"duplicate append id {entry.id}")
            entries.append(entry)
            validate_journal_entries(session_id, entries)
            self._store[session_id] = entries
            self._revision[session_id] = self._revision.get(session_id, 0) + 1

    def save_all(self, session_id: str, entries: list[JournalEntry]) -> None:
        """全量替换 — 仅迁移/测试；正常运行应使用 append_entry。"""
        with _session_lock(f"mem:{session_id}"):
            validate_journal_entries(session_id, entries)
            self._store[session_id] = list(entries)
            self._revision[session_id] = self._revision.get(session_id, 0) + 1


class JsonlJournalRepository:
    """JSONL 仓库 — 单进程 per-session RLock + 行级 append。

    并发边界：仅保证**同进程**内多线程 append 原子性；**不支持**跨进程/多 worker 并发写同一文件。
    跨进程场景需外部分布式锁或换用 DB journal。
    """

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        safe = session_id.replace("/", "_").replace("..", "_")
        return self.base_dir / f"{safe}.jsonl"

    def _lock_key(self, session_id: str) -> str:
        return f"jsonl:{self._path(session_id)}"

    def list_sessions(self) -> list[str]:
        out: list[str] = []
        for p in self.base_dir.glob("*.jsonl"):
            out.append(p.stem)
        return out

    def load(self, session_id: str) -> list[JournalEntry]:
        with _session_lock(self._lock_key(session_id)):
            path = self._path(session_id)
            if not path.exists():
                return []
            entries: list[JournalEntry] = []
            lines = path.read_text(encoding="utf-8").splitlines()
            for i, line in enumerate(lines):
                if not line.strip():
                    continue
                try:
                    data: dict[str, Any] = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise JournalCorruptError(f"corrupt JSON at {path}:{i + 1}: {exc}") from exc
                entries.append(_validate_entry_dict(session_id, data, i + 1))
        validate_journal_entries(session_id, entries)
        return entries

    def append_entry(self, session_id: str, entry: JournalEntry) -> None:
        with _session_lock(self._lock_key(session_id)):
            path = self._path(session_id)
            existing = self.load(session_id) if path.exists() else []
            if any(e.id == entry.id for e in existing):
                raise JournalCorruptError(f"duplicate append id {entry.id}")
            trial = existing + [entry]
            validate_journal_entries(session_id, trial)
            line = json.dumps(entry.to_dict(), ensure_ascii=False) + "\n"
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())

    def save_all(self, session_id: str, entries: list[JournalEntry]) -> None:
        with _session_lock(self._lock_key(session_id)):
            validate_journal_entries(session_id, entries)
            path = self._path(session_id)
            payload = "\n".join(json.dumps(e.to_dict(), ensure_ascii=False) for e in entries)
            if payload:
                payload += "\n"
            fd, tmp = tempfile.mkstemp(dir=self.base_dir, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(payload)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, path)
            except Exception:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
