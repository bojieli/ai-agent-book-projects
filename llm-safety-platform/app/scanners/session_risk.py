"""Multi-turn session risk scorer with session graph (ADR-023/027).

Accumulates turn history, injection/crescendo signals, and role-drift heuristics
when ``session_id`` is present. Store is pluggable (memory|redis-shaped).
"""

from __future__ import annotations

import re

from app.scanners.base import ScanContext, ScanResult
from app.scanners.session_store import (
    SessionGraph,
    TurnRecord,
    get_session_store,
    reset_session_store,
)

__all__ = ["SessionRiskScanner", "reset_session_store", "session_snapshot"]

_INJ_SIGNAL = re.compile(
    r"(?i)(ignore|forget).{0,20}(previous|prior)|system\s*prompt|jailbreak|\bDAN\b|"
    r"developer\s*mode|secret\s*key|exfiltrat|make\s+a\s+bomb|制作炸弹|"
    r"do\s+anything\s+now|unrestricted\s+mode|"
    r"morse\s+code.{0,40}password|Interlace\s+Part|let'?s\s+say\s+i\s+wanted\s+to\s+log",
)
_CRESCENDO = re.compile(
    r"(?i)(step\s*[2-9]|part\s*\d+\s*/\s*\d+|continue\s+(the\s+)?previous|"
    r"第\s*[2-9]\s*/|继续之前|仅学术|hypothetically|for\s+a\s+novel|"
    r"just\s+this\s+once|gradually|一点点|更具体的操作|"
    r"Interlace\s+Part|Part\s*1\s*:.{0,40}Part\s*2|"
    r"step\s+by\s+step.{0,40}(login|bomb|password)|先讨论.{0,20}再|"
    r"更具体的|再详细一点|下一[步轮])",
)
# Role-drift: user tries to become system / force assistant into attacker persona
_ROLE_DRIFT = re.compile(
    r"(?i)(you\s+are\s+now|act\s+as|pretend\s+to\s+be|from\s+now\s+on\s+you|"
    r"\[SYSTEM\]|\[SYSTEM/CONTEXT\]|进入.{0,8}模式|你现在是|"
    r"role\s*:\s*system|assistant\s*:\s*sure,?\s*i\s*will)",
)


def session_snapshot(session_id: str) -> dict:
    g = get_session_store().get(session_id)
    if not g:
        return {}
    return {
        "turns": len(g.turns),
        "inj_hits": g.inj_hits,
        "crescendo_hits": g.crescendo_hits,
        "role_drift_hits": g.role_drift_hits,
        "crescendo_score": g.crescendo_score,
        "reasons": [
            f"turn:{i}:inj={t.inj}:cresc={t.crescendo}:drift={t.role_drift}"
            for i, t in enumerate(g.turns[-8:], 1)
        ],
    }


class SessionRiskScanner:
    """L1 — escalate when a session accumulates injection / crescendo / role-drift."""

    id = "session_risk"
    layer = "L1"

    def scan(self, text: str, ctx: ScanContext) -> ScanResult:
        sid = str((ctx.extra or {}).get("session_id") or "").strip()
        if not sid:
            return ScanResult(self.id, "allow", 0.0, ["session_risk_skipped_no_session"])

        store = get_session_store()
        st = store.get(sid) or SessionGraph(session_id=sid)

        inj = bool(_INJ_SIGNAL.search(text or ""))
        cresc = bool(_CRESCENDO.search(text or ""))
        drift = bool(_ROLE_DRIFT.search(text or ""))

        preview = (text or "")[:160]
        st.turns.append(
            TurnRecord(
                role="user",
                text_preview=preview,
                inj=inj,
                crescendo=cresc,
                role_drift=drift,
            )
        )
        if inj:
            st.inj_hits += 1
        if cresc:
            st.crescendo_hits += 1
        if drift:
            st.role_drift_hits += 1

        # Crescendo score: rising pressure across turns
        st.crescendo_score = min(
            1.0,
            0.25 * st.crescendo_hits
            + 0.15 * max(0, len(st.turns) - 1)
            + 0.2 * st.inj_hits
            + 0.2 * st.role_drift_hits,
        )
        st.last_ts = st.turns[-1].ts
        # Bound history
        if len(st.turns) > 64:
            st.turns = st.turns[-64:]
        store.put(st)

        score = min(
            1.0,
            0.4 * st.inj_hits
            + 0.3 * st.crescendo_hits
            + 0.25 * st.role_drift_hits
            + 0.08 * max(0, len(st.turns) - 2),
        )
        reasons = [
            f"session_turns:{len(st.turns)}",
            f"session_inj_hits:{st.inj_hits}",
            f"session_crescendo_hits:{st.crescendo_hits}",
            f"session_role_drift_hits:{st.role_drift_hits}",
            f"session_crescendo_score:{st.crescendo_score:.2f}",
        ]

        thr = ctx.spec.threshold or 0.7
        combo = st.inj_hits >= 1 and st.crescendo_hits >= 1 and len(st.turns) >= 2
        drift_escalate = st.role_drift_hits >= 1 and st.inj_hits >= 1
        drift_repeat = st.role_drift_hits >= 2 and len(st.turns) >= 2
        crescendo_escalate = st.crescendo_score >= thr and (st.inj_hits + st.crescendo_hits) >= 2
        if combo or drift_escalate or drift_repeat or crescendo_escalate or (
            score >= thr and (st.inj_hits + st.crescendo_hits + st.role_drift_hits) >= 2
        ):
            score = max(score, thr)
            return ScanResult(self.id, "block", score, reasons + ["session_risk_escalated"])
        if score >= max(0.45, thr * 0.6) or st.crescendo_score >= 0.5:
            return ScanResult(self.id, "alert_only", score, reasons)
        return ScanResult(self.id, "allow", score, reasons)
