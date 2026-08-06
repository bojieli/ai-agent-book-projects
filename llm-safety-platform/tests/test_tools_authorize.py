"""安全平台：工具授权干跑不执行副作用。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.tool_runtime import ToolRuntime


def test_authorize_denylist_without_execute():
    rt = ToolRuntime()
    rt.register_defaults()
    out = rt.authorize(
        "shell_exec",
        "r_authz_1",
        {},
        allowlist=["shell_exec"],
        effect_cap="production",
    )
    assert out["decision"] == "block"
    assert out["executed"] is False
    assert rt.audit[-1].error == "authorize_denylist"


def test_authorize_allow_search_kb_no_side_effect():
    rt = ToolRuntime()
    rt.register_defaults()
    out = rt.authorize(
        "search_kb",
        "r_authz_2",
        {"query": "demo"},
        allowlist=["search_kb"],
        effect_cap="observe",
    )
    assert out["decision"] == "allow"
    assert out["executed"] is False
    assert "result" not in out


def test_authorize_business_tool_without_platform_allowlist():
    """纪要君 connector 不在安全平台白名单内，仍可做风险上限判决。"""
    rt = ToolRuntime()
    rt.register_defaults()
    out = rt.authorize(
        "connector.defect.create",
        "r_authz_3",
        {"title": "bug"},
        allowlist=["search_kb"],  # 故意不含 connector
        effect_cap="draft_only",
        enforce_allowlist=False,
    )
    assert out["decision"] == "allow"
    assert out["executed"] is False
