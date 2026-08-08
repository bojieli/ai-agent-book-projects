"""
Test cases for KillBash tool
Tests all features from tools.json
"""

import pytest
from tools.kill_bash_tool import KillBashTool
from tools.bash_tool import BashTool


class TestKillBashTool:
    """Test KillBash tool functionality"""
    
    def test_kill_shell_session(self, system_state):
        """Test killing a shell session"""
        bash_tool = BashTool(system_state)
        kill_tool = KillBashTool(system_state)
        
        # Create a shell session
        bash_tool.execute({"command": "echo test"})
        shell_id = "default"
        
        # Verify session exists
        assert shell_id in system_state.shell_sessions
        
        # Kill the session
        result = kill_tool.execute({
            "shell_id": shell_id
        })
        
        assert result.success
        assert result.data["status"] == "terminated"
        assert shell_id not in system_state.shell_sessions
    
    def test_kill_nonexistent_session(self, system_state):
        """Test error when trying to kill nonexistent session"""
        tool = KillBashTool(system_state)
        
        result = tool.execute({
            "shell_id": "nonexistent_session"
        })
        
        assert "error" in result.data
        assert "not found" in result.data["error"]
    
    def test_shell_id_returned(self, system_state):
        """Test that shell_id is included in response"""
        bash_tool = BashTool(system_state)
        kill_tool = KillBashTool(system_state)
        
        bash_tool.execute({"command": "echo test"})
        
        result = kill_tool.execute({
            "shell_id": "default"
        })
        
        assert result.success
        assert result.data["shell_id"] == "default"
    def test_kill_background_job(self, system_state):
        """Test killing a background job using its background_job_id."""
        bash_tool = BashTool(system_state)
        kill_tool = KillBashTool(system_state)

        res = bash_tool.execute({"command": "sleep 10", "run_in_background": True})
        assert res.success
        bg_id = res.data["background_job_id"]

        result = kill_tool.execute({"shell_id": bg_id})
        assert result.success
        assert result.data["status"] == "terminated"
        assert result.data["shell_id"] == bg_id

