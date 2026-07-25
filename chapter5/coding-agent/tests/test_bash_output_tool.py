"""
Test cases for BashOutput tool
Tests all features from tools.json
"""

import pytest
import time
from pathlib import Path
from tools.bash_output_tool import BashOutputTool
from tools.bash_tool import BashTool


class TestBashOutputTool:
    """Test BashOutput tool functionality"""
    
    def test_retrieve_background_output(self, system_state):
        """Test retrieving output from background job"""
        bash_tool = BashTool(system_state)
        output_tool = BashOutputTool(system_state)
        
        # Start background job
        bash_result = bash_tool.execute({
            "command": "echo 'background output' && sleep 1",
            "run_in_background": True
        })
        
        assert bash_result.success
        bg_id = bash_result.data["background_job_id"]
        
        # Wait a bit for output
        time.sleep(0.5)
        
        # Retrieve output
        result = output_tool.execute({
            "bash_id": bg_id
        })
        
        assert result.success
        assert "background output" in result.data["output"]
    
    def test_filter_parameter(self, system_state):
        """Test optional regex filtering of output"""
        bash_tool = BashTool(system_state)
        output_tool = BashOutputTool(system_state)
        
        # Create background job with mixed output
        bash_result = bash_tool.execute({
            "command": "echo 'ERROR: something' && echo 'INFO: other' && echo 'ERROR: again'",
            "run_in_background": True
        })
        
        bg_id = bash_result.data["background_job_id"]
        time.sleep(0.5)
        
        # Filter for ERROR lines only
        result = output_tool.execute({
            "bash_id": bg_id,
            "filter": "ERROR"
        })
        
        assert result.success
        output_lines = result.data["output"].split('\n')
        # Should only have ERROR lines
        assert all("ERROR" in line or not line.strip() for line in output_lines if line.strip())
    
    def test_nonexistent_bash_id(self, system_state):
        """Test error when bash_id doesn't exist"""
        tool = BashOutputTool(system_state)
        
        result = tool.execute({
            "bash_id": "nonexistent_12345"
        })
        
        assert "error" in result.data
        assert "not found" in result.data["error"].lower()
    
    def test_output_size_tracking(self, system_state):
        """Test that output_size is included in result"""
        bash_tool = BashTool(system_state)
        output_tool = BashOutputTool(system_state)
        
        bash_result = bash_tool.execute({
            "command": "echo 'test output'",
            "run_in_background": True
        })
        
        bg_id = bash_result.data["background_job_id"]
        time.sleep(0.5)
        
        result = output_tool.execute({
            "bash_id": bg_id
        })
        
        assert result.success
        assert "output_size" in result.data
        assert result.data["output_size"] > 0

    def test_background_job_inherits_persistent_environment(self, system_state):
        """Background Bash jobs retain variables exported earlier in the session."""
        bash_tool = BashTool(system_state)
        output_tool = BashOutputTool(system_state)

        bash_tool.execute({"command": "export BACKGROUND_TEST_VALUE=persisted"})
        bash_result = bash_tool.execute({
            "command": "echo $BACKGROUND_TEST_VALUE",
            "run_in_background": True,
        })
        time.sleep(0.5)

        result = output_tool.execute({
            "bash_id": bash_result.data["background_job_id"],
        })

        assert result.success
        assert "persisted" in result.data["output"]
