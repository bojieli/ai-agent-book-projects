"""Mock MCP server — tools/list summary-only + tools/call."""

from __future__ import annotations

from typing import Any

from app.connectors.discovery import sanitize_tool_description
from app.events.enums import PRODUCTION_EFFECT_RANK
from app.harness import ToolRuntime


class MockMcpServer:
    def __init__(self, runtime: ToolRuntime) -> None:
        self.runtime = runtime

    def tools_list(self, *, summary_only: bool = True) -> list[dict[str, Any]]:
        """默认 summary-only；full schema 需 lazy-load。"""
        out: list[dict[str, Any]] = []
        for tool in self.runtime._tools.values():
            desc = tool.mcp_tool_descriptor()
            summary = sanitize_tool_description(desc.get("description", tool.id))
            if summary_only:
                out.append(
                    {
                        "name": tool.id,
                        "summary": summary,
                        "production_effect": tool.production_effect,
                        "schema_ref": f"schema://{tool.id}",
                    }
                )
            else:
                out.append(desc)
        return out

    def tools_call(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        meeting_id: str,
        max_effect: str = "draft_only",
        allowlist: list[str] | None = None,
    ) -> dict[str, Any]:
        return self.runtime.call(
            name,
            meeting_id,
            arguments,
            allowlist=allowlist,
            max_effect=max_effect,
            effect_rank=PRODUCTION_EFFECT_RANK,
            idempotency_key=arguments.get("idempotency_key"),
        )
