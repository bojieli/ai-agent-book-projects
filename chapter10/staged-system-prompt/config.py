"""
配置模块：集中读取环境变量。

阶段化系统提示词附加项目 使用 OpenAI 官方 SDK，所有可调项都通过环境变量注入，
方便切换到兼容 OpenAI 协议的其他厂商（Kimi / Doubao 等）。
"""

import os

try:
    # 允许把配置写在 .env 里（可选依赖）
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv 不是硬性依赖
    pass


def _to_openrouter_model(model: str) -> str:
    """把模型名映射到 OpenRouter 命名空间（用于无 OPENAI_API_KEY 的回退路径）。"""
    if "/" in model:
        return model                      # 已是 OpenRouter 命名空间，原样使用
    if model.startswith("gpt-"):
        return "openai/" + model          # gpt-* -> openai/gpt-*
    if model.startswith("claude-"):
        return "anthropic/claude-opus-4.8"
    return "openai/gpt-5.6-luna"          # 兜底：当前便宜旗舰


class Config:
    """运行时配置。"""

    # 必填：OpenAI API Key（本实验默认用 OPENAI_API_KEY）
    API_KEY: str = os.environ.get("OPENAI_API_KEY", "")

    # 可选：兼容 OpenAI 协议的 base_url，默认官方地址
    BASE_URL: str = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    # 可选：模型名，默认用当前便宜旗舰 gpt-5.6-luna 控制演示成本
    MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-5.6-luna")

    # 采样温度，稍低一些让行为更稳定可复现
    TEMPERATURE: float = float(os.environ.get("OPENAI_TEMPERATURE", "0.3"))

    @classmethod
    def validate(cls) -> None:
        """校验并按需应用通用回退。

        0) gpt-5.x 系列直连 OpenAI 需组织验证（且这类推理模型只接受默认温度），
           因此只要设置了 OPENROUTER_API_KEY，即便同时有 OPENAI_API_KEY，也优先走
           OpenRouter，省去组织验证的麻烦；
        1) 否则有 OPENAI_API_KEY -> 直连 OpenAI（尊重 OPENAI_BASE_URL）；
        2) 否则有 OPENROUTER_API_KEY -> 改走 OpenRouter，并映射模型名；
        3) 都没有则报清晰错误。
        """
        or_key = os.environ.get("OPENROUTER_API_KEY", "")
        # gpt-5.x（含 gpt-5.6-luna 等推理旗舰）优先走 OpenRouter，规避组织验证。
        needs_openrouter = cls.MODEL.startswith("gpt-5") and "/" not in cls.MODEL
        if or_key and (needs_openrouter or not cls.API_KEY):
            cls.API_KEY = or_key
            cls.BASE_URL = "https://openrouter.ai/api/v1"
            cls.MODEL = _to_openrouter_model(cls.MODEL)
            return
        if cls.API_KEY:
            return
        raise SystemExit(
            "错误：未检测到 OPENAI_API_KEY 或 OPENROUTER_API_KEY 环境变量。\n"
            "请先 `export OPENAI_API_KEY=...`（或 OPENROUTER_API_KEY），"
            "或复制 env.example 为 .env 并填写。"
        )
