"""get_command_history(count=0) must return an empty list, not the full history."""
import pytest

from config import Config
from terminal_controller import TerminalController


@pytest.fixture
def tc(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "WORKSPACE_DIR", tmp_path)
    controller = TerminalController()
    controller.command_history = ["cmd0", "cmd1", "cmd2", "cmd3", "cmd4"]
    return controller


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
