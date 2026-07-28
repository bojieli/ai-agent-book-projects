"""
BashOutput tool - Retrieve output from background bash jobs
"""

import os
import re
from typing import Dict, Any
from .base import BaseTool
from .shell_session import get_background_log_path


class BashOutputTool(BaseTool):
    """Retrieves output from running or completed background bash shells"""
    
    @property
    def name(self) -> str:
        return "BashOutput"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get output from background bash job
        
        - Retrieves output from a running or completed background bash shell
        - Takes a bash_id parameter identifying the shell
        - Always returns only new output since the last check
        - Supports optional regex filtering
        """
        bash_id = params["bash_id"]
        filter_pattern = params.get("filter")
        
        log_file = get_background_log_path(bash_id)
        
        if not os.path.exists(log_file):
            return {"error": f"Bash job not found (no output log) for bash_id: {bash_id}"}
        
        try:
            # Return only what has been appended since the last check, as the
            # tool description promises. The offset is per bash_id and lives in
            # SystemState so it survives across calls.
            previous_offset = self.state.bash_output_offsets.get(bash_id, 0)
            if os.path.getsize(log_file) < previous_offset:
                # Log was truncated or rotated — start over rather than
                # seeking past the end and returning nothing forever.
                previous_offset = 0

            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(previous_offset)
                output = f.read()
                self.state.bash_output_offsets[bash_id] = f.tell()

            if filter_pattern:
                # Filter lines matching pattern
                lines = output.split('\n')
                filtered_lines = [line for line in lines if re.search(filter_pattern, line)]
                output = '\n'.join(filtered_lines)
            
            return {
                "bash_id": bash_id,
                "output": output,
                "output_size": len(output)
            }
            
        except Exception as e:
            return {"error": f"Error reading bash output: {str(e)}"}
