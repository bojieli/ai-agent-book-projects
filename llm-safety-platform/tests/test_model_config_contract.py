"""商业模型配置契约必须默认离线、校验安全且不泄露 API Key。"""

from __future__ import annotations

import pytest

from app.config import Settings
from app.providers.proxy import ModelProxy


def test_model_contract_defaults_to_offline_mode():
    settings = Settings()

    assert settings.validate_model_contract() == []
    assert settings.model_public_summary()["configured"] is False


def test_model_contract_rejects_insecure_external_url_and_invalid_budget():
    settings = Settings(
        model_upstream_url="http://commercial.example.com/v1",
        model_name="example-model",
        model_timeout_seconds=0,
        model_max_input_tokens=0,
        model_max_output_tokens=-1,
        model_daily_call_limit=0,
        model_monthly_budget_cny=0,
    )

    errors = settings.validate_model_contract()

    assert any("HTTPS" in error for error in errors)
    assert any("timeout" in error.lower() for error in errors)
    assert any("token" in error for error in errors)
    assert any("DAILY_CALL_LIMIT" in error for error in errors)
    assert any("MONTHLY_BUDGET" in error for error in errors)


def test_model_public_summary_never_contains_api_key():
    settings = Settings(
        model_upstream_url="https://commercial.example.com/v1",
        model_upstream_key="top-secret-key",
        model_name="example-model",
    )

    summary_text = str(settings.model_public_summary())

    assert settings.validate_model_contract() == []
    assert "top-secret-key" not in summary_text
    assert settings.model_public_summary()["credential_configured"] is True


def test_configured_real_model_cannot_bypass_mock_only_allowlist(monkeypatch):
    configured = Settings(
        model_upstream_url="https://commercial.example.com/v1",
        model_upstream_key="top-secret-key",
        model_name="real-model",
    )
    monkeypatch.setattr("app.providers.proxy.settings", configured)

    with pytest.raises(PermissionError, match="not allowlisted"):
        ModelProxy().chat(
            [{"role": "user", "content": "hello"}],
            allowlist=["mock-llm"],
        )
