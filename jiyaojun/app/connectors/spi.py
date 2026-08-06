"""Connector SPI — must be MCP-describable (not private-only)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class McpCapableConnector(Protocol):
    id: str
    production_effect: str

    def execute(self, args: dict[str, Any]) -> dict[str, Any]: ...

    def mcp_tool_descriptor(self) -> dict[str, Any]:
        """OpenAI/MCP tools/list style descriptor."""
        ...


def as_mcp_list(connectors: list[Any]) -> list[dict[str, Any]]:
    out = []
    for c in connectors:
        if not hasattr(c, "mcp_tool_descriptor"):
            raise TypeError(f"connector {getattr(c, 'id', c)} missing mcp_tool_descriptor")
        out.append(c.mcp_tool_descriptor())
    return out
