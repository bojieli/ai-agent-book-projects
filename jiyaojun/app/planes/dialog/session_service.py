"""Dialog 会话服务 — session journal + bounded agent loop + scheduler。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.agents.bounded_loop import BoundedAgentLoop, MockPlanner
from app.connectors.discovery import ConnectorCatalog, ToolDiscoveryService
from app.connectors.mock import MockDefectConnector, MockTaskConnector
from app.harness import ToolRuntime
from app.knowledge.plane import KnowledgePlane
from app.memory.context import build_context
from app.memory.repository import InMemoryJournalRepository, JsonlJournalRepository
from app.memory.session_journal import SessionAccessError, JournalRepository, SessionJournal
from app.planes.dialog.service import DialogPlane
from app.scheduler.tasks import CancellationToken, InProcessScheduler, TaskStatus

_DEFAULT_TOOL_ALLOWLIST = ["connector.defect.create", "connector.task.create"]
_TERMINAL_TASK = frozenset(
    {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.ORPHANED}
)


@dataclass
class _JournalTaskHook:
    repo: JournalRepository

    def on_task_state(self, session_id: str, payload: dict[str, Any]) -> None:
        j = SessionJournal.resume(session_id, self.repo)
        j.append("state", {"task_state": payload})


@dataclass
class DialogSessionService:
    knowledge: KnowledgePlane
    journal_repo: JournalRepository = field(default_factory=InMemoryJournalRepository)
    scheduler: InProcessScheduler = field(default_factory=InProcessScheduler)
    dialog: DialogPlane | None = None
    agent_loop: BoundedAgentLoop | None = None
    _tasks_restored: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.dialog is None:
            self.dialog = DialogPlane(self.knowledge)
        if self.scheduler.journal_hook is None:
            self.scheduler.journal_hook = _JournalTaskHook(self.journal_repo)
        if self.agent_loop is None:
            rt = ToolRuntime()
            rt.register(MockTaskConnector())
            rt.register(MockDefectConnector())
            catalog = ConnectorCatalog()
            catalog.register_from_connector(
                MockDefectConnector(), org_domains=["eng", "business"], scenarios=["*"]
            )
            catalog.register_from_connector(
                MockTaskConnector(), org_domains=["eng", "business"], scenarios=["*"]
            )
            discovery = ToolDiscoveryService(catalog=catalog, min_score=1.0)
            from app.safety.factory import build_safety_gateway

            self.agent_loop = BoundedAgentLoop(
                runtime=rt,
                discovery=discovery,
                planner=MockPlanner(),
                safety_gateway=build_safety_gateway(),
            )
        self._restore_tasks_from_journals()

    @classmethod
    def with_jsonl(cls, knowledge: KnowledgePlane, journal_dir: Path) -> DialogSessionService:
        return cls(knowledge=knowledge, journal_repo=JsonlJournalRepository(journal_dir))

    @classmethod
    def with_settings(
        cls,
        knowledge: KnowledgePlane,
        settings: Any | None = None,
    ) -> DialogSessionService:
        """按基础设施配置装配 journal / scheduler；postgres 时同步任务投影。"""
        from app.config import InfrastructureSettings, settings as default_settings
        from app.runtime.factory import (
            build_journal_repository,
            build_scheduler,
            wrap_task_journal_hook,
        )

        cfg = settings or default_settings
        if not isinstance(cfg, InfrastructureSettings):
            cfg = InfrastructureSettings.from_env()
        repo = build_journal_repository(cfg)
        scheduler = build_scheduler(cfg)
        svc = cls(knowledge=knowledge, journal_repo=repo, scheduler=scheduler)
        # 默认 __post_init__ 已挂 journal hook；postgres 时再包一层投影写入。
        svc.scheduler.journal_hook = wrap_task_journal_hook(
            cfg, svc.scheduler.journal_hook
        )
        return svc

    def _restore_tasks_from_journals(self) -> None:
        if self._tasks_restored:
            return
        latest: dict[str, dict[str, Any]] = {}
        for sid in self.journal_repo.list_sessions():
            try:
                entries = self.journal_repo.load(sid)
            except Exception:
                continue
            meta = SessionJournal.resume(sid, self.journal_repo).session_meta()
            owner = str(meta.get("owner_user_id", ""))
            for e in entries:
                if e.entry_type != "state":
                    continue
                ts = e.payload.get("task_state")
                if not ts or not ts.get("task_id"):
                    continue
                tid = ts["task_id"]
                latest[tid] = {**ts, "session_id": sid, "owner_user_id": ts.get("owner_user_id") or owner}

        for tid, ts in latest.items():
            status = ts.get("status", "pending")
            task = self.scheduler.register_projection(
                task_id=tid,
                session_id=ts["session_id"],
                owner_user_id=ts.get("owner_user_id", ""),
                kind=ts.get("kind", "pipeline"),
                status=status,
                terminal=ts.get("terminal", ""),
            )
            if task.status not in _TERMINAL_TASK:
                task.status = TaskStatus.ORPHANED
                task.terminal = "needs_resume"
                if self.scheduler.journal_hook:
                    self.scheduler.journal_hook.on_task_state(
                        task.session_id,
                        {
                            "task_id": tid,
                            "status": TaskStatus.ORPHANED.value,
                            "terminal": "needs_resume",
                            "owner_user_id": task.owner_user_id,
                        },
                    )
        self._tasks_restored = True

    def mark_orphaned_tasks_on_restart(self) -> int:
        """进程重启后标记未终态任务为 orphaned/needs_resume。"""
        return self.scheduler.mark_orphaned_on_restart()

    def _journal(
        self,
        session_id: str,
        *,
        user_id: str,
        org_domains: list[str],
        is_admin: bool = False,
        create: bool = False,
    ) -> SessionJournal:
        if create:
            j = SessionJournal.open_or_resume(
                session_id,
                self.journal_repo,
                owner_user_id=user_id,
                org_domains=org_domains,
            )
        else:
            j = SessionJournal.resume(session_id, self.journal_repo)
        j.assert_access(user_id=user_id, org_domains=org_domains, is_admin=is_admin)
        return j

    @staticmethod
    def _resolve_allowlist(tool_allowlist: list[str] | None) -> list[str] | None:
        if tool_allowlist is None:
            return list(_DEFAULT_TOOL_ALLOWLIST)
        return list(tool_allowlist)

    @staticmethod
    def _looks_like_tool_task(msg: str) -> bool:
        keys = ("建缺陷", "建任务", "create defect", "create task", "HITL", "人工")
        return any(k.lower() in msg.lower() for k in keys)

    def chat(
        self,
        *,
        session_id: str,
        user_id: str,
        org_domains: list[str],
        message: str,
        scenario: str = "dialog",
        tool_allowlist: list[str] | None = None,
        is_admin: bool = False,
    ) -> dict[str, Any]:
        journal = self._journal(
            session_id,
            user_id=user_id,
            org_domains=org_domains,
            is_admin=is_admin,
            create=True,
        )
        journal.append("message", {"role": "user", "content": message, "user_id": user_id})
        journal.append_compaction_if_needed()

        if self._looks_like_tool_task(message):
            loop = self.agent_loop
            assert loop is not None
            effective = self._resolve_allowlist(tool_allowlist)
            result = loop.run(
                journal=journal,
                need=message,
                org_domains=org_domains,
                scenario=scenario,
                tool_allowlist=effective,
                meeting_id=session_id,
            )
            ctx = build_context(journal)
            return {
                "session_id": session_id,
                "mode": "agent_loop",
                "terminal": result.terminal,
                "answer": result.answer,
                "steps": result.steps,
                "tool_calls": result.tool_calls,
                "events": result.events,
                "context_entries": ctx.total_entries,
                "path_length": ctx.path_length,
                "memory_kind": "session_journal",
            }

        reply = self.dialog.ask(user_id=user_id, org_domains=org_domains, query=message)
        journal.append(
            "message",
            {"role": "assistant", "content": reply.text, "faithfulness": reply.faithfulness},
        )
        ctx = build_context(journal)
        return {
            "session_id": session_id,
            "mode": "rag_grounding",
            "terminal": "succeeded",
            "answer": reply.text,
            "citations": reply.citations,
            "faithfulness": reply.faithfulness,
            "context_entries": ctx.total_entries,
            "memory_kind": "session_journal",
        }

    def resume_hitl(
        self,
        *,
        session_id: str,
        user_id: str,
        org_domains: list[str],
        message: str,
        approved: bool = True,
        scenario: str = "dialog",
        tool_allowlist: list[str] | None = None,
        is_admin: bool = False,
    ) -> dict[str, Any]:
        journal = self._journal(
            session_id,
            user_id=user_id,
            org_domains=org_domains,
            is_admin=is_admin,
        )
        loop = self.agent_loop
        assert loop is not None
        result = loop.resume(
            journal=journal,
            need=message or "continue",
            org_domains=org_domains,
            scenario=scenario,
            tool_allowlist=tool_allowlist,
            meeting_id=session_id,
            hitl_approved=approved,
            user_id=user_id,
        )
        return {
            "session_id": session_id,
            "mode": "agent_loop_resume",
            "terminal": result.terminal,
            "answer": result.answer,
            "events": result.events,
        }

    def submit_pipeline_background(
        self,
        *,
        session_id: str,
        user_id: str,
        org_domains: list[str],
        fn,
        is_admin: bool = False,
    ) -> str:
        self._journal(
            session_id,
            user_id=user_id,
            org_domains=org_domains,
            is_admin=is_admin,
            create=True,
        )

        def wrapped(task, token: CancellationToken):
            token.check()
            return fn(token)

        t = self.scheduler.submit(
            session_id=session_id,
            kind="pipeline",
            fn=wrapped,
            owner_user_id=user_id,
        )
        journal = SessionJournal.resume(session_id, self.journal_repo)
        journal.append(
            "state",
            {
                "background_task_id": t.task_id,
                "kind": "pipeline",
                "owner_user_id": user_id,
            },
        )
        return t.task_id

    def _assert_task_access(
        self,
        task_id: str,
        *,
        user_id: str,
        is_admin: bool = False,
    ) -> None:
        t = self.scheduler.status(task_id)
        if is_admin:
            return
        if t.owner_user_id and t.owner_user_id != user_id:
            raise SessionAccessError(f"task owner mismatch: {t.owner_user_id} != {user_id}")

    def task_status(
        self,
        task_id: str,
        *,
        user_id: str,
        is_admin: bool = False,
    ) -> dict[str, Any]:
        self._assert_task_access(task_id, user_id=user_id, is_admin=is_admin)
        t = self.scheduler.status(task_id)
        return {
            "task_id": t.task_id,
            "session_id": t.session_id,
            "status": t.status.value,
            "terminal": t.terminal,
            "result": t.result,
            "error": t.error,
            "owner_user_id": t.owner_user_id,
        }

    def cancel_task(
        self,
        task_id: str,
        *,
        user_id: str,
        is_admin: bool = False,
    ) -> dict[str, Any]:
        self._assert_task_access(task_id, user_id=user_id, is_admin=is_admin)
        t = self.scheduler.cancel(task_id)
        return {"task_id": t.task_id, "terminal": t.terminal, "status": t.status.value}

    def get_context(
        self,
        session_id: str,
        *,
        user_id: str,
        org_domains: list[str],
        is_admin: bool = False,
    ) -> dict[str, Any]:
        journal = self._journal(
            session_id,
            user_id=user_id,
            org_domains=org_domains,
            is_admin=is_admin,
        )
        ctx = build_context(journal)
        return {
            "session_id": session_id,
            "active_leaf_id": ctx.active_leaf_id,
            "compaction_summaries": ctx.compaction_summaries,
            "recent_count": len(ctx.recent_entries),
            "total_entries": ctx.total_entries,
            "path_length": ctx.path_length,
            "owner_user_id": journal.session_meta().get("owner_user_id"),
        }

    def fork_branch(
        self,
        session_id: str,
        entry_id: str,
        *,
        user_id: str,
        org_domains: list[str],
        is_admin: bool = False,
    ) -> dict[str, Any]:
        journal = self._journal(
            session_id,
            user_id=user_id,
            org_domains=org_domains,
            is_admin=is_admin,
        )
        branch = journal.fork_from(entry_id)
        return {
            "session_id": session_id,
            "branch_id": branch.id,
            "active_leaf_id": journal.active_leaf_id,
        }
