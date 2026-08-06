"""基础设施配置必须离线安全、可校验且不泄露凭据。"""

from __future__ import annotations

from app.config import InfrastructureSettings


def test_default_infrastructure_settings_are_offline_safe():
    settings = InfrastructureSettings()

    assert settings.validate() == []
    assert settings.public_summary()["database_enabled"] is False
    assert settings.public_summary()["redis_enabled"] is False


def test_infrastructure_settings_reject_invalid_urls_and_schemes():
    settings = InfrastructureSettings(
        database_url="sqlite:///unsafe.db",
        redis_url="http://redis:6379",
        s3_endpoint="not-a-url",
        qdrant_url="qdrant:6333",
        safety_gateway_url="ftp://safety",
    )

    errors = settings.validate()

    assert len(errors) == 6
    assert any("PostgreSQL" in error for error in errors)
    assert any("JIYAOJUN_CELERY_BROKER_URL" in error for error in errors)
    assert any("JIYAOJUN_SAFETY_GATEWAY_URL" in error for error in errors)


def test_public_summary_never_contains_secret_values():
    settings = InfrastructureSettings(
        s3_access_key="access-secret",
        s3_secret_key="storage-secret",
        safety_gateway_token="gateway-secret",
    )

    summary_text = str(settings.public_summary())

    assert "access-secret" not in summary_text
    assert "storage-secret" not in summary_text
    assert "gateway-secret" not in summary_text
    assert settings.public_summary()["credentials_configured"] is True
