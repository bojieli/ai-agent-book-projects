"""M5：故障矩阵与遥测。"""

from __future__ import annotations

from app.eval.fault_matrix import run_fault_matrix
from app.observability.telemetry import Telemetry, SPAN_MODEL


def test_fault_matrix_all_scenarios_pass():
    report = run_fault_matrix()
    assert report["ok"] is True, report
    assert report["total"] == 7
    assert report["passed"] == 7


def test_telemetry_prometheus_and_spans():
    tel = Telemetry()
    span = tel.start_span(SPAN_MODEL, meeting_id="m1", trace_id="t1")
    tel.end_span(span, status="ok")
    tel.emit("demo.event", terminal="succeeded", trace_id="t1")
    text = tel.render_prometheus()
    assert "jiyaojun_events_total" in text
    assert len(tel.obs.spans) == 1
    assert tel.obs.spans[0].ended_at is not None
