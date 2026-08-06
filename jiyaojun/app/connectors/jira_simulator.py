"""Jira 确定性模拟器 — 幂等、超时、失败、状态流转与 webhook 回调。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from app.connectors.persistent_defect import PersistentDefectConnector

# 终态：与 BFF webhook 关闭 Continuum 语义对齐
TERMINAL_STATUSES = frozenset({"closed", "done", "resolved"})


@dataclass
class JiraSimulator:
    """可配置模式的 Jira 外部系统模拟；支持幂等建单与异步回调模拟。"""

    backend: PersistentDefectConnector | None = None
    mode: str = "normal"  # normal | timeout | fail
    issues: dict[str, dict[str, Any]] = field(default_factory=dict)
    issue_status: dict[str, str] = field(default_factory=dict)
    _pending_callbacks: list[tuple[Callable[[dict[str, Any]], Any], dict[str, Any]]] = field(
        default_factory=list, repr=False
    )

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        """创建或复用缺陷单；timeout/fail 模式不写入存储。"""
        mode = str(args.get("mode", self.mode)).lower()
        if mode == "timeout":
            return {"ok": False, "error": "timeout"}
        if mode == "fail":
            return {"ok": False, "error": "jira_create_failed"}

        key = args.get("idempotency_key") or str(uuid.uuid4())
        if key in self.issues:
            return dict(self.issues[key])

        if self.backend is not None:
            raw = self.backend.execute(
                {
                    "title": args["title"],
                    "idempotency_key": key,
                    "status": args.get("status", "open"),
                }
            )
        else:
            external_id = f"BUG-{len(self.issues) + 1:04d}"
            raw = {
                "external_id": external_id,
                "status": args.get("status", "open"),
                "title": args["title"],
                "idempotency_key": key,
                "production_effect": "draft_only",
            }

        shaped = self._shape_issue(raw, project=args.get("project", "ENG"))
        self.issues[key] = shaped
        self.issue_status[shaped["jira_key"]] = str(shaped.get("status", "open"))
        return dict(shaped)

    def transition(self, issue_key: str, status: str) -> dict[str, Any]:
        """流转缺陷状态：open / in_progress / done / closed 等。"""
        if issue_key not in self.issue_status:
            raise KeyError(f"unknown issue: {issue_key}")
        self.issue_status[issue_key] = status
        for stored in self.issues.values():
            if stored.get("jira_key") == issue_key:
                stored["status"] = status
                ext = stored.get("external_id")
                idem = stored.get("idempotency_key")
                if self.backend is not None and idem:
                    self.backend.sync_status(idem, status)
                if ext:
                    self.issue_status[ext] = status
        return {"ok": True, "jira_key": issue_key, "status": status}

    def schedule_webhook_callback(
        self,
        handler: Callable[[dict[str, Any]], Any],
        payload: dict[str, Any],
    ) -> None:
        """登记 webhook 回调（测试可 flush_callbacks 同步触发）。"""
        self._pending_callbacks.append((handler, dict(payload)))

    def emit_callback(
        self,
        handler: Callable[[dict[str, Any]], Any],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """立即触发一次外部状态回调。"""
        handler(dict(payload))
        return {"ok": True, "emitted": True}

    def flush_callbacks(self) -> int:
        """执行所有已登记的 webhook 回调，返回触发次数。"""
        pending = list(self._pending_callbacks)
        self._pending_callbacks.clear()
        for handler, payload in pending:
            handler(payload)
        return len(pending)

    def get_by_idempotency(self, idempotency_key: str) -> dict[str, Any] | None:
        """按幂等键查询已创建缺陷。"""
        return self.issues.get(idempotency_key)

    def _shape_issue(self, raw: dict[str, Any], *, project: str) -> dict[str, Any]:
        external_id = raw["external_id"]
        jira_key = external_id.replace("BUG-", f"{project}-")
        return {
            **raw,
            "ok": True,
            "jira_key": jira_key,
            "project": project,
            "self": f"https://jira.mock.local/browse/{jira_key}",
        }
