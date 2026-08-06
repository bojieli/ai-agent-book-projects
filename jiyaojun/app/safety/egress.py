"""商业模型数据出站门禁（ADR-0003）。"""

from __future__ import annotations

from dataclasses import dataclass
import re

# 允许脱敏后出站
_EGRESS_OK = frozenset({"public", "internal"})
# 禁止出站（含密封会议）
_EGRESS_BLOCK = frozenset({"confidential", "critical", "sealed"})

# 明显凭据 / 真实身份模式（确定性规则先行）
_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[a-z0-9\-._~+/]+=*"),
    re.compile(r"\b\d{17}[\dXx]\b"),  # 粗粒度身份证
)


@dataclass(frozen=True)
class EgressDecision:
    """出站判决结果。"""

    allowed: bool
    decision: str  # allow | redact | block
    reason: str
    redacted_text: str
    external_provider_calls: int = 0  # 高敏路径必须保持 0


def _redact_secrets(text: str) -> tuple[str, bool]:
    """脱敏明显凭据；返回 (文本, 是否发生了脱敏)。"""
    out = text
    changed = False
    for pat in _SECRET_PATTERNS:
        new, n = pat.subn("[REDACTED]", out)
        if n:
            changed = True
            out = new
    return out, changed


def evaluate_egress(
    *,
    classification: str,
    text: str,
    sealed: bool = False,
) -> EgressDecision:
    """
    public/internal：脱敏后允许出站；
    confidential/critical/sealed：阻断，external_provider_calls 固定为 0。
    """
    cls = (classification or "internal").strip().lower()
    if sealed or cls in _EGRESS_BLOCK or cls == "sealed":
        return EgressDecision(
            allowed=False,
            decision="block",
            reason=f"egress_blocked:{cls or 'sealed'}",
            redacted_text="",
            external_provider_calls=0,
        )
    if cls not in _EGRESS_OK:
        # 未知分级 fail-closed
        return EgressDecision(
            allowed=False,
            decision="block",
            reason=f"egress_unknown_classification:{cls}",
            redacted_text="",
            external_provider_calls=0,
        )
    redacted, changed = _redact_secrets(text)
    return EgressDecision(
        allowed=True,
        decision="redact" if changed else "allow",
        reason="egress_ok_redacted" if changed else "egress_ok",
        redacted_text=redacted,
        external_provider_calls=0,  # 计数由网关在实际上游调用时累加
    )
