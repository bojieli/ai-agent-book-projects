"""env.example 与 config.py 的一致性（离线）。"""

import re
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent


def _env_names(text: str):
    return {
        m.group(1)
        for m in re.finditer(r"^#?\s*([A-Z][A-Z0-9_]+)=", text, re.MULTILINE)
    }


def test_env_example_lists_required_keys():
    names = _env_names((PROJECT_DIR / "env.example").read_text(encoding="utf-8"))
    for key in ("KIMI_API_KEY", "DASHSCOPE_API_KEY", "GEMINI_API_KEY", "SILICONFLOW_API_KEY"):
        assert key in names, f"env.example 缺少 {key}"


def test_env_example_has_no_real_secret():
    text = (PROJECT_DIR / "env.example").read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.lstrip("# ").strip()
        if "=" in line:
            value = line.split("=", 1)[1].strip()
            assert value.startswith("your-") or value == "" or "://" in value or value.isdigit() or "*" in value or re.fullmatch(r"[A-Za-z0-9._\-/]+", value), (
                f"env.example 疑似写入真实密钥: {line}"
            )


def test_config_required_env_matches_validate():
    from config import Config

    assert set(Config.required_env()) == {
        "KIMI_API_KEY", "DASHSCOPE_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"
    }
