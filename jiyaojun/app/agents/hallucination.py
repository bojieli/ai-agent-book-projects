"""Hallucination / fabrication guards (mock detector)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HallucinationReport:
    flagged: bool
    reasons: list[str]


def detect_hallucination(
    *,
    artifact_payload: dict,
    source_quotes: list[str],
    invented_numbers: bool = False,
) -> HallucinationReport:
    reasons: list[str] = []
    text = str(artifact_payload)
    if invented_numbers:
        reasons.append("numeric_invention")
    # claim without any overlapping source token
    if source_quotes:
        joined = " ".join(source_quotes)
        # crude: if payload claims 100% and sources don't
        if "100%" in text and "100%" not in joined:
            reasons.append("unsupported_stat")
    if "根据我的理解随便写的" in text:
        reasons.append("explicit_fabrication")
    return HallucinationReport(flagged=bool(reasons), reasons=reasons)
