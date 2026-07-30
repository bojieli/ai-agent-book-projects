"""Asynchronous, timestamped point-to-point bus for the two live Agents."""

from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, List, Optional

from models import AgentMessage


class MessageBus:
    def __init__(self, trace_path: Optional[str] = None):
        self.started = time.monotonic()
        self._sequence = 0
        self._queues: DefaultDict[str, asyncio.Queue[AgentMessage]] = defaultdict(asyncio.Queue)
        self.history: List[AgentMessage] = []
        self.trace_path = Path(trace_path) if trace_path else None

    async def send(
        self,
        sender: str,
        recipient: str,
        type: str,
        *,
        sensitive_keys: tuple[str, ...] = (),
        **payload,
    ) -> AgentMessage:
        self._sequence += 1
        message = AgentMessage(
            sender=sender,
            recipient=recipient,
            type=type,
            payload=payload,
            sequence=self._sequence,
            monotonic_seconds=round(time.monotonic() - self.started, 6),
            wall_time=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
        self.history.append(message)
        await self._queues[recipient].put(message)
        printable = {k: ("<redacted>" if k in sensitive_keys else v) for k, v in payload.items()}
        # Keep the redaction policy beside the in-memory envelope. The receiver gets
        # the value, while console/disk traces never retain spoken personal data.
        setattr(message, "_sensitive_keys", sensitive_keys)
        print(
            f"[t={message.monotonic_seconds:8.3f}s #{message.sequence:03d}] "
            f"{sender} -> {recipient} | {type} | "
            f"{json.dumps(printable, ensure_ascii=False)}"
        )
        self.flush()
        return message

    async def receive(self, recipient: str, timeout: Optional[float] = None) -> AgentMessage:
        get = self._queues[recipient].get()
        return await asyncio.wait_for(get, timeout) if timeout else await get

    def flush(self) -> None:
        if not self.trace_path:
            return
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for message in self.history:
            row = message.to_dict()
            keys = getattr(message, "_sensitive_keys", ())
            row["payload"] = {
                k: ("<redacted>" if k in keys else v) for k, v in row["payload"].items()
            }
            rows.append(row)
        self.trace_path.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
