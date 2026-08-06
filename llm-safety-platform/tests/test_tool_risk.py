"""ADR-019 tool risk: denylist, dangerous op recognition, audit."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from app.policy import PolicyEngine
from app.tool_runtime import (
    PLATFORM_TOOL_DENYLIST,
    ConfirmRequiredError,
    ToolRiskClassifier,
    ToolRiskRule,
    ToolRuntime,
)


def test_platform_denylist_blocks_even_if_allowlisted():
    rt = ToolRuntime()
    rt.register_defaults()
    with pytest.raises(PermissionError, match="denylist"):
        rt.call(
            "shell_exec",
            "r1",
            {},
            allowlist=["shell_exec"],
            effect_cap="production",
            denylist=[],
        )
    assert rt.audit[-1].error == "denylist"
    assert "shell_exec" in PLATFORM_TOOL_DENYLIST


def test_evil_email_blocked_by_risk_rule():
    eng = PolicyEngine()
    eng.load_yaml_dir()
    b = eng.resolve("t_demo", "customer_bot")
    rt = ToolRuntime()
    rt.register_defaults()
    with pytest.raises(PermissionError, match="dangerous"):
        rt.call(
            "send_email",
            "r2",
            {"to": "attacker@evil.com"},
            allowlist=b.tool_allowlist,
            effect_cap="production",  # raise cap for this unit test
            denylist=b.tool_denylist,
            risk_rules=b.tool_risk_rules,
            email_domain_allowlist=b.email_domain_allowlist,
        )
    assert rt.audit[-1].decision == "block"
    assert "email_evil" in rt.audit[-1].matched_rules


def test_external_email_requires_confirm():
    eng = PolicyEngine()
    eng.load_yaml_dir()
    b = eng.resolve("t_demo", "customer_bot")
    rt = ToolRuntime()
    rt.register_defaults()
    with pytest.raises(ConfirmRequiredError) as ei:
        rt.call(
            "send_email",
            "r3",
            {"to": "someone@gmail.com"},
            allowlist=b.tool_allowlist,
            effect_cap="production",
            denylist=b.tool_denylist,
            risk_rules=b.tool_risk_rules,
            email_domain_allowlist=b.email_domain_allowlist,
        )
    assert ei.value.risk.decision == "confirm_only"
    assert rt.audit[-1].error == "confirm_required"


def test_internal_email_allowed_and_audited():
    eng = PolicyEngine()
    eng.load_yaml_dir()
    b = eng.resolve("t_demo", "customer_bot")
    rt = ToolRuntime()
    rt.register_defaults()
    out = rt.call(
        "send_email",
        "r4",
        {"to": "a@webank.com"},
        allowlist=b.tool_allowlist,
        effect_cap="production",
        denylist=b.tool_denylist,
        risk_rules=b.tool_risk_rules,
        email_domain_allowlist=b.email_domain_allowlist,
    )
    assert out.get("sent") is True
    assert rt.audit[-1].error is None


def test_denylist_cannot_shrink_on_publish():
    eng = PolicyEngine()
    eng.load_yaml_dir()
    with pytest.raises(ValueError, match="denylist"):
        eng.publish(
            tenant_id="t_demo",
            app_id="customer_bot",
            reason="bad",
            tool_denylist=[],  # shrink
            tool_allowlist=["search_kb"],
        )


def test_classifier_url_rule():
    c = ToolRiskClassifier()
    rules = [
        ToolRiskRule(
            id="u1",
            tool_id="fetch_url",
            field="url",
            type="url_is_ip_or_non_https",
            op_risk_tier="medium",
            decision="alert_only",
        )
    ]
    a = c.assess("fetch_url", {"url": "http://10.0.0.1/x"}, rules=rules)
    assert a.decision == "alert_only"
    assert a.matched_rules == ["u1"]
