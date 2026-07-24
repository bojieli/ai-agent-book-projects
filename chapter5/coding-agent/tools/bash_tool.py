"""
Bash tool - Command execution in persistent shell sessions
"""

import time
import hashlib
from typing import Dict, Any
from .base import BaseTool


class BashTool(BaseTool):
    """Executes bash commands in persistent shell sessions"""
    
    @property
    def name(self) -> str:
        return "Bash"
    
    def _execute_impl(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute bash command in persistent shell
        
        - Commands execute in a persistent shell session
        - Working directory changes persist across commands
        - Environment variables persist
        - Supports background execution with run_in_background parameter
        - Output truncated if exceeds 30000 characters
        """
        command = params["command"]
        timeout_ms = params.get("timeout")
        # None/<=0: treat like omit. Exact 0 used to become timeout=0s and drop all output.
        if timeout_ms is None or timeout_ms <= 0:
            timeout_ms = 120000
        timeout = timeout_ms / 1000  # Convert ms to seconds
        run_in_background = params.get("run_in_background", False)
        
        # Get or create shell session
        shell_id = self.state.default_shell_id
        if shell_id not in self.state.shell_sessions:
            from .shell_session import ShellSession
            self.state.shell_sessions[shell_id] = ShellSession(
                session_id=shell_id,
                current_directory=self.state.current_directory
            )
        
        session = self.state.shell_sessions[shell_id]
        
        if run_in_background:
            # Start a separate native-shell process. ShellSession handles the
            # platform-specific invocation and log location.
            bg_id = f"bg_{int(time.time())}_{hashlib.md5(command.encode()).hexdigest()[:8]}"
            pid = session.start_background(command, bg_id)
            
            return {
                "output": f"Background job started with ID: {bg_id}\nPID: {pid}",
                "exit_code": 0,
                "shell_id": shell_id,
                "background_job_id": bg_id
            }
        else:
            # Execute command synchronously
            output, exit_code = session.execute(command, timeout=timeout)
            
            # Update system state directory
            self.state.current_directory = session.current_directory
            
            # Truncate output if too long
            if len(output) > 30000:
                output = output[:30000] + f"\n... (output truncated, {len(output)} total characters)"
            
            return {
                "output": output,
                "exit_code": exit_code,
                "shell_id": shell_id,
                "working_directory": session.current_directory
            }
