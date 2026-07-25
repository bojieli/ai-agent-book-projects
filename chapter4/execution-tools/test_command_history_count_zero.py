"""get_command_history(count=0) must return an empty list, not the full history."""
import asyncio
import sys
import tempfile
import shutil
from pathlib import Path

import pytest


class Config:
    WORKSPACE_DIR = Path(tempfile.mkdtemp())
    AUTO_VERIFY_CODE = False
    REQUIRE_APPROVAL_FOR_DANGEROUS_OPS = False


sys.modules["config"] = type(sys)("config")
sys.modules["config"].Config = Config

from terminal_controller import TerminalController


@pytest.fixture
def tc():
    Config.WORKSPACE_DIR = Path(tempfile.mkdtemp())
    controller = TerminalController()
    controller.command_history = ["cmd0", "cmd1", "cmd2", "cmd3", "cmd4"]
    yield controller
    if Config.WORKSPACE_DIR.exists():
        shutil.rmtree(Config.WORKSPACE_DIR, ignore_errors=True)


@pytest.mark.asyncio
async def test_count_zero_returns_empty_history(tc):
    result = await tc.get_command_history(count=0)
    assert result["success"] is True
    assert result["history"] == []
    assert result["count"] == 0
    assert result["total"] == 5


@pytest.mark.asyncio
async def test_positive_count_still_returns_recent(tc):
    result = await tc.get_command_history(count=2)
    assert result["success"] is True
    assert result["history"] == ["cmd3", "cmd4"]
    assert result["count"] == 2
    assert result["total"] == 5
