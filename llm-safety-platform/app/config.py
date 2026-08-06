"""Runtime configuration (env-driven)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


def _b(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes", "on")


def _is_secure_or_local_url(value: str) -> bool:
    """商业端点必须使用 HTTPS；仅本机/容器内服务允许 HTTP。"""
    if not value:
        return True
    parsed = urlparse(value)
    if parsed.scheme == "https" and parsed.netloc:
        return True
    host = parsed.hostname or ""
    return parsed.scheme == "http" and (
        host in {"localhost", "127.0.0.1", "::1"}
        or ("." not in host and bool(host))
    )


@dataclass(frozen=True)
class Settings:
    app_name: str = "llm-safety-platform"
    database_url: str = "sqlite:///./data/safety.db"
    redis_url: str = ""  # empty → in-memory quota
    master_key: str = "dev-only-change-me-32bytes-key!!"
    scanner_mode: str = "shim"  # shim|onnx|remote|llm_guard
    content_rules_path: str = ""
    classifier_url: str = ""
    onnx_model_path: str = ""
    llm_guard_path: str = ""
    oidc_issuer: str = ""
    oidc_audience: str = "llm-safety"
    oidc_jwks_url: str = ""
    oidc_disabled: bool = True  # local/CI: use admin bearer
    oidc_required: bool = False  # fail-closed JWT when set
    admin_token: str = "admin-dev-token"
    siem_webhook_url: str = ""
    siem_sink: str = "log"  # log|http|file
    kms_provider: str = "env"  # env|file|aws_kms_stub|http_kms
    dual_llm: bool = False
    session_store: str = "memory"  # memory|redis
    otel_enabled: bool = False
    default_rpm: int = 120
    model_upstream_url: str = ""
    model_upstream_key: str = ""
    model_failover_url: str = ""
    model_name: str = ""
    model_timeout_seconds: float = 5.0
    model_max_input_tokens: int = 8192
    model_max_output_tokens: int = 2048
    model_daily_call_limit: int = 100
    model_monthly_budget_cny: float = 200.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.getenv("SAFETY_DATABASE_URL", cls.database_url),
            redis_url=os.getenv("SAFETY_REDIS_URL", ""),
            master_key=os.getenv("SAFETY_MASTER_KEY", cls.master_key),
            scanner_mode=os.getenv("SAFETY_SCANNER_MODE", "shim"),
            content_rules_path=os.getenv("SAFETY_CONTENT_RULES_PATH", ""),
            classifier_url=os.getenv("SAFETY_CLASSIFIER_URL", ""),
            onnx_model_path=os.getenv("SAFETY_ONNX_MODEL_PATH", ""),
            llm_guard_path=os.getenv("SAFETY_LLM_GUARD_PATH", ""),
            oidc_issuer=os.getenv("SAFETY_OIDC_ISSUER", ""),
            oidc_audience=os.getenv("SAFETY_OIDC_AUDIENCE", "llm-safety"),
            oidc_jwks_url=os.getenv("SAFETY_OIDC_JWKS_URL", ""),
            oidc_disabled=_b("SAFETY_OIDC_DISABLED", "1"),
            oidc_required=_b("OIDC_REQUIRED", "0") or _b("SAFETY_OIDC_REQUIRED", "0"),
            admin_token=os.getenv("SAFETY_ADMIN_TOKEN", "admin-dev-token"),
            siem_webhook_url=os.getenv("SAFETY_SIEM_WEBHOOK_URL", ""),
            siem_sink=os.getenv("SAFETY_SIEM_SINK", "log"),
            kms_provider=os.getenv("SAFETY_KMS_PROVIDER", "env"),
            dual_llm=_b("SAFETY_DUAL_LLM", "0") or _b("DUAL_LLM", "0"),
            session_store=os.getenv("SAFETY_SESSION_STORE", "memory"),
            otel_enabled=_b("SAFETY_OTEL_ENABLED", "0"),
            default_rpm=int(os.getenv("SAFETY_DEFAULT_RPM", "120")),
            model_upstream_url=os.getenv(
                "SAFETY_MODEL_UPSTREAM_URL", os.getenv("MODEL_BASE_URL", "")
            ).strip(),
            model_upstream_key=os.getenv(
                "SAFETY_MODEL_UPSTREAM_KEY", os.getenv("MODEL_API_KEY", "")
            ).strip(),
            model_failover_url=os.getenv("SAFETY_MODEL_FAILOVER_URL", ""),
            model_name=os.getenv(
                "SAFETY_MODEL_NAME", os.getenv("MODEL_NAME", "")
            ).strip(),
            model_timeout_seconds=float(
                os.getenv(
                    "SAFETY_MODEL_TIMEOUT_SECONDS",
                    os.getenv("MODEL_TIMEOUT_SECONDS", "5"),
                )
            ),
            model_max_input_tokens=int(
                os.getenv(
                    "SAFETY_MODEL_MAX_INPUT_TOKENS",
                    os.getenv("MODEL_MAX_INPUT_TOKENS", "8192"),
                )
            ),
            model_max_output_tokens=int(
                os.getenv(
                    "SAFETY_MODEL_MAX_OUTPUT_TOKENS",
                    os.getenv("MODEL_MAX_OUTPUT_TOKENS", "2048"),
                )
            ),
            model_daily_call_limit=int(
                os.getenv(
                    "SAFETY_MODEL_DAILY_CALL_LIMIT",
                    os.getenv("MODEL_DAILY_CALL_LIMIT", "100"),
                )
            ),
            model_monthly_budget_cny=float(
                os.getenv(
                    "SAFETY_MODEL_MONTHLY_BUDGET_CNY",
                    os.getenv("MODEL_MONTHLY_BUDGET_CNY", "200"),
                )
            ),
        )

    def validate_model_contract(self) -> list[str]:
        """校验商业模型配置；真实调用前必须 fail-closed。"""
        errors: list[str] = []
        for name, value in (
            ("SAFETY_MODEL_UPSTREAM_URL", self.model_upstream_url),
            ("SAFETY_MODEL_FAILOVER_URL", self.model_failover_url),
        ):
            if not _is_secure_or_local_url(value):
                errors.append(f"{name} must use HTTPS or a local HTTP endpoint")
        if self.model_upstream_url and not self.model_name:
            errors.append("SAFETY_MODEL_NAME is required for a configured upstream")
        if self.model_timeout_seconds <= 0:
            errors.append("SAFETY_MODEL_TIMEOUT_SECONDS must be positive")
        if self.model_max_input_tokens <= 0 or self.model_max_output_tokens <= 0:
            errors.append("model token limits must be positive")
        if self.model_daily_call_limit <= 0:
            errors.append("SAFETY_MODEL_DAILY_CALL_LIMIT must be positive")
        if self.model_monthly_budget_cny <= 0:
            errors.append("SAFETY_MODEL_MONTHLY_BUDGET_CNY must be positive")
        return errors

    def model_public_summary(self) -> dict[str, object]:
        """返回可观测配置，不输出 API Key。"""
        return {
            "configured": bool(self.model_upstream_url and self.model_name),
            "upstream_url": self.model_upstream_url,
            "model_name": self.model_name,
            "timeout_seconds": self.model_timeout_seconds,
            "max_input_tokens": self.model_max_input_tokens,
            "max_output_tokens": self.model_max_output_tokens,
            "daily_call_limit": self.model_daily_call_limit,
            "monthly_budget_cny": self.model_monthly_budget_cny,
            "credential_configured": bool(self.model_upstream_key),
        }


settings = Settings.from_env()
