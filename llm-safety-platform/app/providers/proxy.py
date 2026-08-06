"""ModelProxy — mock + OpenAI-compatible upstream with failover."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from app.config import settings
from app.providers.mock import MockModelProvider


class ModelProxy:
    id = "model-proxy"

    def __init__(self) -> None:
        self._mock = MockModelProvider()

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str = "mock-llm",
        allowlist: list[str] | tuple[str, ...] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        if (
            model == "mock-llm"
            and settings.model_upstream_url
            and settings.model_name
        ):
            model = settings.model_name
        # 离线 mock 始终可用；真实模型必须逐个出现在 allowlist 中。
        if (
            model != "mock-llm"
            and allowlist is not None
            and model not in allowlist
        ):
            raise PermissionError(f"model not allowlisted: {model}")
        meta: dict[str, Any] = {
            "model": model,
            "upstream": "mock",
            "tokens": max(1, len(str(messages)) // 4),
        }
        if not settings.model_upstream_url or model == "mock-llm":
            return self._mock.chat(messages), meta
        contract_errors = settings.validate_model_contract()
        if contract_errors:
            raise ValueError("; ".join(contract_errors))
        try:
            text = self._call(
                settings.model_upstream_url,
                settings.model_upstream_key,
                messages,
                model,
            )
            meta["upstream"] = "primary"
            return text, meta
        except Exception as primary_err:  # noqa: BLE001
            if settings.model_failover_url:
                text = self._call(
                    settings.model_failover_url,
                    settings.model_upstream_key,
                    messages,
                    model,
                )
                meta["upstream"] = "failover"
                meta["primary_error"] = str(primary_err)
                return text, meta
            raise

    def _call(
        self,
        base: str,
        key: str,
        messages: list[dict[str, str]],
        model: str,
    ) -> str:
        url = base.rstrip("/") + "/chat/completions"
        body = json.dumps(
            {
                "model": model,
                "messages": messages,
                "max_tokens": settings.model_max_output_tokens,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}" if key else "",
            },
            method="POST",
        )
        with urllib.request.urlopen(
            req, timeout=settings.model_timeout_seconds
        ) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]
