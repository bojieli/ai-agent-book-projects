"""按配置构建安全网关：默认离线，配置了 URL 则走 HTTP。"""

from __future__ import annotations

from typing import Any

from app.safety.budget import ModelBudgetTracker
from app.safety.http_client import HttpSafetyGateway
from app.safety.offline import OfflineSafetyGateway


def build_safety_gateway(settings: Any | None = None) -> OfflineSafetyGateway | HttpSafetyGateway:
    """
    无 JIYAOJUN_SAFETY_GATEWAY_URL → OfflineSafetyGateway（确定性，run_all 全绿）。
    有 URL → HttpSafetyGateway（Bearer 虚拟密钥）。
    """
    from app.config import InfrastructureSettings, settings as default_settings

    cfg = settings or default_settings
    if not isinstance(cfg, InfrastructureSettings):
        cfg = InfrastructureSettings.from_env()
    budget = ModelBudgetTracker(
        max_input_tokens=getattr(cfg, "model_max_input_tokens", 8192),
        max_output_tokens=getattr(cfg, "model_max_output_tokens", 2048),
        daily_call_limit=getattr(cfg, "model_daily_call_limit", 100),
        monthly_budget_cny=float(getattr(cfg, "model_monthly_budget_cny", 200.0)),
    )
    if cfg.safety_gateway_url:
        errors = cfg.validate()
        if errors:
            raise ValueError("; ".join(errors))
        return HttpSafetyGateway(
            cfg.safety_gateway_url,
            cfg.safety_gateway_token,
            budget=budget,
        )
    return OfflineSafetyGateway(budget=budget)
