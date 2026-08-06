"""Deterministic extractive summarizer for session compaction。"""

from __future__ import annotations

from typing import Any, Protocol


class Summarizer(Protocol):
    def summarize(
        self,
        entries: list[Any],
        *,
        prior_summary: str | None = None,
    ) -> str: ...


class DeterministicExtractiveSummarizer:
    """从 message/tool 条目抽取关键词片段；迭代时合并 prior_summary。"""

    def summarize(
        self,
        entries: list[Any],
        *,
        prior_summary: str | None = None,
    ) -> str:
        parts: list[str] = []
        if prior_summary:
            parts.append(f"[prior] {prior_summary[:200]}")
        for e in entries:
            if e.entry_type == "message":
                p = e.payload
                role = p.get("role", "?")
                content = str(p.get("content", ""))[:80].strip()
                if content:
                    parts.append(f"{role}:{content}")
            elif e.entry_type == "tool_result":
                tid = e.payload.get("tool_id", "tool")
                ext = e.payload.get("result", {}).get("external_id", "")
                parts.append(f"tool:{tid}→{ext}")
        if not parts:
            return prior_summary or "(empty)"
        body = " | ".join(parts[:8])
        return body[:400]
