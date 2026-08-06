"""ToolRuntime — sole side-effect path (ADR-008 + ADR-019)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.policy.binding import EFFECT_RANK
from app.tool_runtime.risk_classifier import RiskAssessment, ToolRiskClassifier, ToolRiskRule

# Platform hard denylist — cannot be overridden by app allowlist (ADR-019)
PLATFORM_TOOL_DENYLIST = frozenset(
    {"shell_exec", "transfer_money_unrestricted", "os_system", "kubectl_exec"}
)


class ConfirmRequiredError(PermissionError):
    """Raised when ToolRiskClassifier requires human approval before execute."""

    def __init__(self, message: str, *, risk: RiskAssessment) -> None:
        super().__init__(message)
        self.risk = risk


class Connector(Protocol):
    id: str
    production_effect: str

    def execute(self, args: dict[str, Any]) -> dict[str, Any]: ...


@dataclass
class ToolCallRecord:
    call_id: str
    tool_id: str
    request_id: str
    args: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    production_effect: str
    op_risk_tier: str = "low"
    decision: str = "allow"
    matched_rules: list[str] = field(default_factory=list)
    ts: float = field(default_factory=time.time)


class SearchKbConnector:
    id = "search_kb"
    production_effect = "observe"

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"hits": [{"title": "demo", "q": args.get("query", "")}]}


class SendEmailConnector:
    id = "send_email"
    production_effect = "production"

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"sent": True, "to": args.get("to")}


class FetchUrlConnector:
    id = "fetch_url"
    production_effect = "observe"

    def execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "url": args.get("url", ""),
            "content": args.get("simulated_content", ""),
        }


class ToolRuntime:
    def __init__(
        self,
        mcp_allowlist: list[str] | None = None,
        classifier: ToolRiskClassifier | None = None,
    ) -> None:
        self._tools: dict[str, Connector] = {}
        self.audit: list[ToolCallRecord] = []
        self._seen_idem: set[str] = set()
        self.mcp_allowlist = set(mcp_allowlist or ["search_kb", "fetch_url", "send_email"])
        self.classifier = classifier or ToolRiskClassifier()

    def register(self, connector: Connector) -> None:
        self._tools[connector.id] = connector

    def register_defaults(self) -> None:
        self.register(SearchKbConnector())
        self.register(SendEmailConnector())
        self.register(FetchUrlConnector())

    def filter_mcp_tools(self, tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for t in tools:
            name = t.get("name") or t.get("id") or ""
            if name in self.mcp_allowlist and name not in PLATFORM_TOOL_DENYLIST:
                out.append(t)
        return out

    def _audit(
        self,
        *,
        tool_id: str,
        request_id: str,
        args: dict[str, Any],
        result: dict[str, Any] | None,
        error: str | None,
        production_effect: str,
        risk: RiskAssessment | None = None,
    ) -> ToolCallRecord:
        rec = ToolCallRecord(
            call_id=str(uuid.uuid4()),
            tool_id=tool_id,
            request_id=request_id,
            args=args,
            result=result,
            error=error,
            production_effect=production_effect,
            op_risk_tier=(risk.op_risk_tier if risk else "low"),
            decision=(risk.decision if risk else ("block" if error else "allow")),
            matched_rules=list(risk.matched_rules) if risk else [],
        )
        self.audit.append(rec)
        return rec

    def authorize(
        self,
        tool_id: str,
        request_id: str,
        args: dict[str, Any],
        *,
        allowlist: tuple[str, ...] | list[str],
        effect_cap: str,
        denylist: tuple[str, ...] | list[str] | None = None,
        risk_rules: tuple[ToolRiskRule, ...] | list[ToolRiskRule] | None = None,
        email_domain_allowlist: tuple[str, ...] | list[str] | None = None,
        enforce_allowlist: bool = False,
    ) -> dict[str, Any]:
        """
        仅做授权判决，不执行工具（供业务侧本地执行前调用）。

        默认 enforce_allowlist=False：只施加平台 denylist / 风险规则 /（若本地注册）effect_cap，
        不要求工具出现在安全平台业务白名单——业务权限由调用方自行判定（ADR-0001）。
        """
        app_deny = set(denylist or [])
        if tool_id in PLATFORM_TOOL_DENYLIST or tool_id in app_deny:
            risk = RiskAssessment("critical", "block", ["denylist"], ["platform_or_app_deny"])
            self._audit(
                tool_id=tool_id,
                request_id=request_id,
                args=args,
                result=None,
                error="authorize_denylist",
                production_effect="none",
                risk=risk,
            )
            return {
                "request_id": request_id,
                "decision": "block",
                "risk": risk.as_dict(),
                "executed": False,
            }

        if enforce_allowlist and tool_id not in allowlist:
            risk = RiskAssessment("high", "block", ["not_in_allowlist"], [])
            self._audit(
                tool_id=tool_id,
                request_id=request_id,
                args=args,
                result=None,
                error="authorize_not_in_allowlist",
                production_effect="none",
                risk=risk,
            )
            return {
                "request_id": request_id,
                "decision": "block",
                "risk": risk.as_dict(),
                "executed": False,
            }

        tool = self._tools.get(tool_id)
        effect = tool.production_effect if tool is not None else "none"
        if tool is not None and EFFECT_RANK[tool.production_effect] > EFFECT_RANK[effect_cap]:
            risk = RiskAssessment("high", "block", ["effect_cap_exceeded"], [])
            self._audit(
                tool_id=tool_id,
                request_id=request_id,
                args=args,
                result=None,
                error="authorize_effect_cap",
                production_effect=effect,
                risk=risk,
            )
            return {
                "request_id": request_id,
                "decision": "block",
                "risk": risk.as_dict(),
                "executed": False,
            }

        # 未知业务工具仍可按规则做风险上限判决（业务侧本地执行）。
        risk = self.classifier.assess(
            tool_id,
            args,
            rules=risk_rules or (),
            email_domain_allowlist=email_domain_allowlist or (),
        )
        self._audit(
            tool_id=tool_id,
            request_id=request_id,
            args=args,
            result=None,
            error=None if risk.decision in ("allow", "alert_only") else f"authorize_{risk.decision}",
            production_effect=effect,
            risk=risk,
        )
        return {
            "request_id": request_id,
            "decision": risk.decision,
            "risk": risk.as_dict(),
            "executed": False,
        }

    def call(
        self,
        tool_id: str,
        request_id: str,
        args: dict[str, Any],
        *,
        allowlist: tuple[str, ...] | list[str],
        effect_cap: str,
        denylist: tuple[str, ...] | list[str] | None = None,
        risk_rules: tuple[ToolRiskRule, ...] | list[ToolRiskRule] | None = None,
        email_domain_allowlist: tuple[str, ...] | list[str] | None = None,
        idempotency_key: str | None = None,
        skip_risk_execute_gate: bool = False,
    ) -> dict[str, Any]:
        """
        L4: denylist → allowlist → effect_cap → risk classify → execute?
        Always audits. confirm_only raises ConfirmRequiredError (no execute).
        """
        app_deny = set(denylist or [])
        if tool_id in PLATFORM_TOOL_DENYLIST or tool_id in app_deny:
            risk = RiskAssessment("critical", "block", ["denylist"], ["platform_or_app_deny"])
            self._audit(
                tool_id=tool_id,
                request_id=request_id,
                args=args,
                result=None,
                error="denylist",
                production_effect="none",
                risk=risk,
            )
            raise PermissionError(f"tool denylisted: {tool_id}")

        if tool_id not in allowlist:
            risk = RiskAssessment("high", "block", ["not_in_allowlist"], [])
            self._audit(
                tool_id=tool_id,
                request_id=request_id,
                args=args,
                result=None,
                error="not_in_allowlist",
                production_effect="none",
                risk=risk,
            )
            raise PermissionError(f"tool not in allowlist: {tool_id}")

        tool = self._tools.get(tool_id)
        if tool is None:
            raise KeyError(f"unknown tool: {tool_id}")

        if EFFECT_RANK[tool.production_effect] > EFFECT_RANK[effect_cap]:
            risk = RiskAssessment("high", "block", ["effect_cap_exceeded"], [])
            self._audit(
                tool_id=tool_id,
                request_id=request_id,
                args=args,
                result=None,
                error="effect_cap_exceeded",
                production_effect=tool.production_effect,
                risk=risk,
            )
            raise PermissionError(
                f"tool effect {tool.production_effect} exceeds cap {effect_cap}"
            )

        risk = self.classifier.assess(
            tool_id,
            args,
            rules=risk_rules or (),
            email_domain_allowlist=email_domain_allowlist or (),
        )

        if risk.decision == "block" and not skip_risk_execute_gate:
            self._audit(
                tool_id=tool_id,
                request_id=request_id,
                args=args,
                result=None,
                error="risk_block",
                production_effect=tool.production_effect,
                risk=risk,
            )
            raise PermissionError(
                f"dangerous operation blocked: {','.join(risk.reason_codes) or risk.op_risk_tier}"
            )

        if risk.decision == "confirm_only" and not skip_risk_execute_gate:
            self._audit(
                tool_id=tool_id,
                request_id=request_id,
                args=args,
                result=None,
                error="confirm_required",
                production_effect=tool.production_effect,
                risk=risk,
            )
            raise ConfirmRequiredError(
                f"dangerous operation requires approval: {','.join(risk.matched_rules)}",
                risk=risk,
            )

        if idempotency_key:
            if idempotency_key in self._seen_idem:
                return {"deduped": True, "risk": risk.as_dict()}
            self._seen_idem.add(idempotency_key)

        result = tool.execute(dict(args))
        self._audit(
            tool_id=tool_id,
            request_id=request_id,
            args=args,
            result=result,
            error=None,
            production_effect=tool.production_effect,
            risk=risk,
        )
        out = dict(result)
        out["_risk"] = risk.as_dict()
        return out
