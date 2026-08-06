"""轻量遥测：进程内 span/metrics；可选 OTLP HTTP 导出（无 SDK 依赖）。"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.observability.ledger import Observability, TraceSpan


# 覆盖 ADR 要求的关键路径名
SPAN_MODEL = "safety.model"
SPAN_RAG = "rag.retrieve"
SPAN_HITL = "hitl.gate"
SPAN_TOOL_AUTHZ = "safety.tool_authorize"
SPAN_WRITEBACK = "tool.writeback"


@dataclass
class TelemetryEvent:
    """结构化审计/观测事件。"""

    event_type: str
    terminal: str = ""
    trace_id: str = ""
    attrs: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


class Telemetry:
    """
    默认纯内存（run_all 零依赖）。
    设置 JIYAOJUN_OTEL_ENDPOINT（如 http://127.0.0.1:54318）时尝试 OTLP/HTTP 导出 traces。
    """

    def __init__(self, obs: Observability | None = None) -> None:
        self.obs = obs or Observability()
        self.events: list[TelemetryEvent] = []
        self._counters: dict[str, float] = defaultdict(float)
        self.otlp_endpoint = os.getenv("JIYAOJUN_OTEL_ENDPOINT", "").strip()
        self.export_errors: list[str] = []

    def start_span(
        self,
        name: str,
        meeting_id: str = "",
        trace_id: str = "",
        **attrs: Any,
    ) -> TraceSpan:
        tid = trace_id or str(uuid.uuid4())
        return self.obs.start_span(name, meeting_id or "n/a", tid, **attrs)

    def end_span(self, span: TraceSpan, *, status: str = "ok", **attrs: Any) -> None:
        span.end(status=status, **attrs)
        metric = 'jiyaojun_span_total{{name="{}",status="{}"}}'.format(span.name, status)
        self.inc(metric)
        if self.otlp_endpoint:
            self._export_span(span, status=status)

    def emit(
        self,
        event_type: str,
        *,
        terminal: str = "",
        trace_id: str = "",
        **attrs: Any,
    ) -> TelemetryEvent:
        ev = TelemetryEvent(
            event_type=event_type,
            terminal=terminal,
            trace_id=trace_id or str(uuid.uuid4()),
            attrs=dict(attrs),
        )
        self.events.append(ev)
        self.inc('jiyaojun_events_total{{type="{}"}}'.format(event_type))
        if terminal:
            self.inc('jiyaojun_terminal_total{{terminal="{}"}}'.format(terminal))
        return ev

    def inc(self, name: str, value: float = 1.0) -> None:
        self._counters[name] += value

    def render_prometheus(self) -> str:
        """Prometheus text exposition（演示用）。"""
        lines = [
            "# HELP jiyaojun_events_total Meeting assistant telemetry events",
            "# TYPE jiyaojun_events_total counter",
        ]
        for k, v in sorted(self._counters.items()):
            lines.append(f"{k} {v}")
        return "\n".join(lines) + "\n"

    def _export_span(self, span: TraceSpan, *, status: str) -> None:
        """最小 OTLP/HTTP JSON（不引入 opentelemetry SDK）。失败只记日志，不阻断业务。"""
        ended = span.ended_at or time.time()
        start_ns = int(span.started_at * 1_000_000_000)
        end_ns = int(ended * 1_000_000_000)
        body = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": "jiyaojun"}}
                        ]
                    },
                    "scopeSpans": [
                        {
                            "spans": [
                                {
                                    "traceId": span.trace_id.replace("-", "")[:32].ljust(32, "0"),
                                    "spanId": span.span_id.replace("-", "")[:16].ljust(16, "0"),
                                    "name": span.name,
                                    "kind": 1,
                                    "startTimeUnixNano": str(start_ns),
                                    "endTimeUnixNano": str(end_ns),
                                    "attributes": [
                                        {
                                            "key": "meeting.id",
                                            "value": {"stringValue": span.meeting_id},
                                        },
                                        {
                                            "key": "status",
                                            "value": {"stringValue": status},
                                        },
                                    ],
                                    "status": {
                                        "code": 1 if status == "ok" else 2,
                                    },
                                }
                            ]
                        }
                    ],
                }
            ]
        }
        url = self.otlp_endpoint.rstrip("/") + "/v1/traces"
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=1.5)  # noqa: S310
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            self.export_errors.append(str(exc))


# 进程级默认实例，供故障矩阵与运行时共享
default_telemetry = Telemetry()
