"""Null optional language must default to python on public paths."""
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from multilang_executor import LanguageExecutor
from execution_tools import ExecutionTools


def test_null_language_executor_defaults_to_python():
    le = LanguageExecutor(workspace_dir=Path(tempfile.mkdtemp()))
    result = asyncio.run(le.execute_code("print(42)", language=None, timeout=10))
    assert isinstance(result, dict)
    assert result.get("language") == "python"
    assert "42" in (result.get("stdout") or "")


def test_null_language_code_interpreter_defaults(monkeypatch):
    """Public MCP path: ExecutionTools.code_interpreter(language=None)."""
    helper = MagicMock()
    et = ExecutionTools(helper)
    seen = {}

    async def fake_exec(code, language, timeout=30.0, stdin=None, files=None):
        seen["language"] = language
        return {
            "success": True,
            "stdout": "ok\n",
            "stderr": "",
            "language": language,
            "returncode": 0,
            "status": "ok",
        }

    monkeypatch.setattr(et.lang_executor, "execute_code", fake_exec)
    import config as cfg
    monkeypatch.setattr(cfg.Config, "AUTO_VERIFY_CODE", False, raising=False)
    monkeypatch.setattr(cfg.Config, "REQUIRE_APPROVAL_FOR_DANGEROUS_OPS", False, raising=False)
    monkeypatch.setattr(cfg.Config, "AUTO_SUMMARIZE_COMPLEX_OUTPUT", False, raising=False)

    out = asyncio.run(et.code_interpreter("print(1)", language=None))
    assert seen["language"] == "python"
    assert out["language"] == "python"
    assert out.get("error") in (None, "")
