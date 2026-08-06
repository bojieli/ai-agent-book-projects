"""Chart binding — only from chart_series / declared fields; never invent."""

from __future__ import annotations

from typing import Any


def render_charts(acl_view_artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for a in acl_view_artifacts:
        series = a.get("chart_series")
        if not series:
            out.append({"chart_id": None, "status": "data_insufficient", "message": "数据不足"})
            continue
        for s in series:
            if "points" not in s or not s["points"]:
                out.append(
                    {
                        "chart_id": s.get("series_id"),
                        "status": "data_insufficient",
                        "message": "数据不足",
                    }
                )
            else:
                out.append(
                    {
                        "chart_id": s.get("series_id"),
                        "status": "ok",
                        "label": s.get("label"),
                        "points": s["points"],
                        "unit": s.get("unit"),
                    }
                )
    return out


def invent_chart_forbidden(points_from_llm: list[Any] | None) -> None:
    if points_from_llm is not None:
        raise ValueError("forbidden: invent chart points outside Artifact.chart_series")
