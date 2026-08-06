"""Mock WeCom (企微) channel + Mock Jira — swap for real later."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid

from app.connectors.jira_simulator import JiraSimulator
from app.connectors.persistent_defect import PersistentDefectConnector


@dataclass
class MockWeComClient:
    """Simulates enterprise WeChat bot/app messaging."""

    sent: list[dict[str, Any]] = field(default_factory=list)

    def send_markdown(self, *, touser: list[str], content: str, meeting_id: str) -> dict[str, Any]:
        if not touser:
            return {"ok": False, "errcode": 400, "errmsg": "empty touser"}
        msg = {
            "msgid": f"wx_{uuid.uuid4().hex[:10]}",
            "touser": touser,
            "msgtype": "markdown",
            "content": content[:2000],
            "meeting_id": meeting_id,
        }
        self.sent.append(msg)
        return {"ok": True, "msgid": msg["msgid"]}


@dataclass
class MockJiraConnector:
    """Jira-shaped SPI — 委托 JiraSimulator（幂等 / 超时 / 失败 / 回调）。"""

    backend: PersistentDefectConnector | None = None
    simulator: JiraSimulator | None = None
    id: str = "connector.jira.issue.create"
    production_effect: str = "draft_only"
    mode: str = "normal"

    def __post_init__(self) -> None:
        if self.simulator is None:
            self.simulator = JiraSimulator(backend=self.backend, mode=self.mode)

    def mcp_tool_descriptor(self) -> dict[str, Any]:
        return {
            "name": self.id,
            "description": "Mock Jira issue create",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "idempotency_key": {"type": "string"},
                    "project": {"type": "string"},
                    "mode": {"type": "string", "enum": ["normal", "timeout", "fail"]},
                },
                "required": ["title"],
            },
        }

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.simulator.execute(args)

    def transition(self, issue_key: str, status: str) -> dict[str, Any]:
        """流转 Jira 缺陷状态。"""
        return self.simulator.transition(issue_key, status)

    def schedule_webhook_callback(self, handler, payload: dict[str, Any]) -> None:
        """登记 webhook 回调。"""
        self.simulator.schedule_webhook_callback(handler, payload)

    def emit_callback(self, handler, payload: dict[str, Any]) -> dict[str, Any]:
        """立即触发 webhook 回调。"""
        return self.simulator.emit_callback(handler, payload)
