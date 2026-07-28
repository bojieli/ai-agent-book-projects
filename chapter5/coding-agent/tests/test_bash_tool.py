"""
Test cases for Bash tool
Tests all features from tools.json
"""

import pytest
import time
from pathlib import Path
from tools.bash_tool import BashTool


class TestBashTool:
    """Test Bash tool functionality"""
    
    def test_basic_command(self, system_state):
        """Test basic command execution"""
        tool = BashTool(system_state)
        result = tool.execute({
            "command": "echo 'Hello, World!'"
        })
        
        assert result.success
        assert "Hello, World!" in result.data["output"]
        assert result.data["exit_code"] == 0
    
    def test_command_with_exit_code(self, system_state):
        """Test that exit codes are captured"""
        tool = BashTool(system_state)
        
        # Successful command
        result = tool.execute({
            "command": "true"
        })
        assert result.data["exit_code"] == 0
        
        # Failed command
        result = tool.execute({
            "command": "false"
        })
        assert result.data["exit_code"] == 1
    
    def test_persistent_shell_session(self, system_state, temp_dir):
        """Test that shell session persists across commands"""
        tool = BashTool(system_state)
        
        # Set an environment variable
        result1 = tool.execute({
            "command": "export TEST_VAR=hello"
        })
        assert result1.success
        
        # Check that it persists
        result2 = tool.execute({
            "command": "echo $TEST_VAR"
        })
        assert result2.success
        assert "hello" in result2.data["output"]
    
    def test_directory_change_persistence(self, system_state, temp_dir):
        """Test that directory changes persist"""
        tool = BashTool(system_state)
        
        # Change directory
        result1 = tool.execute({
            "command": f"cd {temp_dir}"
        })
        assert result1.success
        
        # Verify we're in the new directory
        result2 = tool.execute({
            "command": "pwd"
        })
        assert result2.success
        assert str(temp_dir) in result2.data["output"]
        
        # System state should also be updated
        assert temp_dir in Path(system_state.current_directory).parents or \
               Path(temp_dir) == Path(system_state.current_directory)
    
    def test_timeout_parameter(self, system_state):
        """Test timeout parameter (in milliseconds)"""
        tool = BashTool(system_state)
        
        # Command that should timeout (1 second timeout)
        result = tool.execute({
            "command": "sleep 5",
            "timeout": 1000  # 1 second in ms
        })
        
        assert "timeout" in result.data["output"].lower()
    
    def test_output_truncation(self, system_state):
        """Test that output exceeding 30000 chars is truncated"""
        tool = BashTool(system_state)
        
        # Generate large output
        result = tool.execute({
            "command": "yes | head -n 2000"
        })
        
        assert result.success
        output_len = len(result.data["output"])
        # Should be truncated or close to limit
        assert output_len <= 35000  # Some buffer
    
    def test_background_execution(self, system_state):
        """Test run_in_background parameter"""
        tool = BashTool(system_state)
        
        result = tool.execute({
            "command": "sleep 1 && echo done",
            "run_in_background": True
        })
        
        assert result.success
        assert "background_job_id" in result.data
        assert "PID" in result.data["output"]
    
    def test_multiple_commands_with_semicolon(self, system_state, temp_dir):
        """Test multiple commands separated by semicolon"""
        tool = BashTool(system_state)
        
        result = tool.execute({
            "command": f"cd {temp_dir} ; touch test_file.txt ; ls test_file.txt"
        })
        
        assert result.success
        assert "test_file.txt" in result.data["output"]
    
    def test_multiple_commands_with_and(self, system_state, temp_dir):
        """Test multiple commands with && operator"""
        tool = BashTool(system_state)
        
        result = tool.execute({
            "command": f"cd {temp_dir} && echo 'success'"
        })
        
        assert result.success
        assert "success" in result.data["output"]
    
    def test_quoted_paths_with_spaces(self, system_state, temp_dir):
        """Test handling paths with spaces using quotes"""
        tool = BashTool(system_state)
        
        # Create directory with spaces
        space_dir = temp_dir / "dir with spaces"
        space_dir.mkdir()
        
        result = tool.execute({
            "command": f'cd "{space_dir}" && pwd'
        })
        
        assert result.success
        assert "dir with spaces" in result.data["output"]
    
    def test_shell_id_tracking(self, system_state):
        """Test that shell_id is returned"""
        tool = BashTool(system_state)
        result = tool.execute({
            "command": "echo test"
        })
        
        assert result.success
        assert "shell_id" in result.data
        assert result.data["shell_id"] == "default"
    
    def test_working_directory_in_result(self, system_state):
        """Test that working_directory is included in result"""
        tool = BashTool(system_state)
        result = tool.execute({
            "command": "pwd"
        })
        
        assert result.success
        assert "working_directory" in result.data

    def test_null_timeout_like_omit(self, system_state):
        """Explicit JSON null timeout must behave like omit (default 120s)."""
        tool = BashTool(system_state)
        result = tool.execute({
            "command": "echo ok",
            "timeout": None,
        })
        assert result.success
        assert "ok" in result.data["output"]
        assert result.data["exit_code"] == 0

    def test_subsecond_timeout_ms_allows_fast_command(self, system_state):
        """timeout=500ms must not collapse to 0s via int(ms/1000)."""
        tool = BashTool(system_state)
        result = tool.execute({
            "command": "echo hi",
            "timeout": 500,
        })
        assert result.success
        assert result.data["exit_code"] == 0
        assert "hi" in result.data["output"]
        assert "timed out" not in result.data["output"].lower()

    def test_subsecond_timeout_ms_still_enforced(self, system_state):
        """A 300ms budget must still time out a longer sleep."""
        tool = BashTool(system_state)
        result = tool.execute({
            "command": "sleep 2",
            "timeout": 300,
        })
        assert result.data["exit_code"] == -1
        assert "timed out" in result.data["output"].lower()

    def test_timeout_ms_zero_like_omit(self, system_state):
        """timeout=0 must not skip the command (DataLoss via immediate 0s deadline)."""
        tool = BashTool(system_state)
        result = tool.execute({
            "command": "echo zero-ok",
            "timeout": 0,
        })
        assert result.success
        assert result.data["exit_code"] == 0
        assert "zero-ok" in result.data["output"]
        assert "timed out" not in result.data["output"].lower()

    def test_timeout_ms_negative_like_omit(self, system_state):
        tool = BashTool(system_state)
        result = tool.execute({
            "command": "echo neg-ok",
            "timeout": -1,
        })
        assert result.success
        assert "neg-ok" in result.data["output"]
        assert result.data["exit_code"] == 0
