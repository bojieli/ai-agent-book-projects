"""M3：安全接入、出站门禁、双重授权与预算。"""

from __future__ import annotations

from app.safety.budget import ModelBudgetTracker
from app.safety.decisions import max_strict
from app.safety.dual_authz import authorize_tool_dual, combine_business_and_safety
from app.safety.egress import evaluate_egress
from app.safety.factory import build_safety_gateway
from app.safety.http_client import HttpSafetyGateway
from app.safety.model_client import SafetyRoutedLLMClient
from app.safety.offline import OfflineSafetyGateway
from app.safety.protocol import ToolAuthorizeResult
from app.config import InfrastructureSettings


def test_max_strict_picks_stricter_decision():
    assert max_strict(["allow", "block"]) == "block"
    assert max_strict(["allow", "confirm_only"]) == "confirm_only"
    assert max_strict(["unknown", "allow"]) == "block"


def test_egress_blocks_confidential_and_critical():
    for cls in ("confidential", "critical", "sealed"):
        d = evaluate_egress(classification=cls, text="hello secret")
        assert d.allowed is False
        assert d.decision == "block"
        assert d.external_provider_calls == 0


def test_egress_allows_internal_with_redaction():
    d = evaluate_egress(
        classification="internal",
        text="please use api_key=sk-live-abc123 for demo",
    )
    assert d.allowed is True
    assert d.decision == "redact"
    assert "sk-live" not in d.redacted_text
    assert "[REDACTED]" in d.redacted_text


def test_offline_chat_high_sens_never_calls_external():
    gw = OfflineSafetyGateway()
    out = gw.chat_completions(
        messages=[{"role": "user", "content": "密封会议内容"}],
        classification="critical",
    )
    assert out.decision == "block"
    assert gw.external_provider_calls == 0
    assert out.external_provider_calls == 0


def test_offline_chat_internal_uses_deterministic_provider():
    gw = OfflineSafetyGateway()
    out = gw.chat_completions(
        messages=[{"role": "user", "content": "请总结会议"}],
        classification="internal",
    )
    assert out.decision == "allow"
    assert out.upstream == "offline"
    assert gw.external_provider_calls == 0


def test_budget_exhausted_fail_closed():
    budget = ModelBudgetTracker(daily_call_limit=1)
    budget.daily_calls = 1
    gw = OfflineSafetyGateway(budget=budget)
    out = gw.chat_completions(
        messages=[{"role": "user", "content": "再问一次"}],
        classification="public",
    )
    assert out.decision == "block"
    assert out.blocked_reason == "daily_call_limit"


def test_dual_authz_business_deny_cannot_be_granted_by_safety():
    gw = OfflineSafetyGateway()
    dual = authorize_tool_dual(
        gw,
        tool_id="connector.defect.create",
        arguments={"title": "x"},
        granted_ids=[],  # 业务拒绝
        org_domain="eng",
        policy_binding="test/binding",
    )
    assert dual.allowed is False
    assert dual.final_decision == "block"
    assert dual.reason == "business_denied"


def test_dual_authz_safety_block_overrides_business_allow():
    safety = ToolAuthorizeResult(decision="block", request_id="r1", executed=False)
    dual = combine_business_and_safety(business_decision="allow", safety=safety)
    assert dual.allowed is False
    assert dual.final_decision == "block"


def test_dual_authz_gateway_failure_fail_closed():
    safety = ToolAuthorizeResult(
        decision="block",
        fail_closed=True,
        message="down",
        executed=False,
    )
    dual = combine_business_and_safety(business_decision="allow", safety=safety)
    assert dual.allowed is False
    assert dual.reason == "safety_fail_closed"


def test_dual_authz_meeting_tool_allowed_offline():
    gw = OfflineSafetyGateway()
    dual = authorize_tool_dual(
        gw,
        tool_id="connector.defect.create",
        arguments={"title": "缺陷"},
        granted_ids=["connector.defect.create"],
        trace_id="t1",
        org_domain="eng",
        policy_binding="jiyaojun/test",
    )
    assert dual.allowed is True
    assert dual.final_decision == "allow"
    assert dual.audit["trace_id"] == "t1"
    assert dual.safety is not None
    assert dual.safety.executed is False


def test_http_gateway_fail_closed_on_unreachable():
    gw = HttpSafetyGateway("http://127.0.0.1:1", timeout_seconds=0.2)
    out = gw.chat_completions(
        messages=[{"role": "user", "content": "hi"}],
        classification="internal",
    )
    assert out.decision == "block"
    assert out.blocked_reason == "safety_gateway_unavailable"
    auth = gw.authorize_tool(tool_id="connector.task.create", arguments={})
    assert auth.decision == "block"
    assert auth.fail_closed is True
    assert auth.executed is False


def test_factory_default_is_offline():
    gw = build_safety_gateway(InfrastructureSettings())
    assert isinstance(gw, OfflineSafetyGateway)


def test_factory_with_url_is_http():
    gw = build_safety_gateway(
        InfrastructureSettings(safety_gateway_url="http://127.0.0.1:8080")
    )
    assert isinstance(gw, HttpSafetyGateway)


def test_safety_routed_llm_client_blocks_critical():
    client = SafetyRoutedLLMClient(
        OfflineSafetyGateway(), classification="critical"
    )
    resp = client.complete("sys", "user confidential")
    assert resp.verdict == "fail"
    assert client.calls[-1]["external_provider_calls"] == 0


def test_config_exposes_budget_without_secrets():
    s = InfrastructureSettings(
        safety_gateway_token="secret-token",
        model_daily_call_limit=50,
    )
    summary = s.public_summary()
    assert summary["model_daily_call_limit"] == 50
    assert "secret-token" not in str(summary)
