"""Generic execution tools: code interpreter and virtual terminal."""

import os
import subprocess
import sys
import io
import tempfile
import traceback
from typing import Dict, Any, Optional, Tuple
from contextlib import redirect_stdout, redirect_stderr
from llm_helper import LLMHelper
from config import Config
from multilang_executor import LanguageExecutor, ExecutionStatus

# Long-output handling thresholds (see "长输出的截断与持久化" in chapter 4).
# When output exceeds either threshold, keep the head and tail few lines in the
# context and persist the full output to a temp file for later retrieval.
MAX_OUTPUT_LINES = 200
MAX_OUTPUT_CHARS = 10000
HEAD_LINES = 50
TAIL_LINES = 50


def truncate_and_persist(
    text: str,
    tool_name: str = "execution",
    max_lines: int = MAX_OUTPUT_LINES,
    max_chars: int = MAX_OUTPUT_CHARS,
    head_lines: int = HEAD_LINES,
    tail_lines: int = TAIL_LINES,
) -> Tuple[str, Optional[str]]:
    """Truncate over-long output and persist the full text to a temp file.

    Returns a tuple of (processed_text, saved_path). When the output is within
    both thresholds, it is returned unchanged with ``saved_path`` set to None.
    Otherwise only the first ``head_lines`` and last ``tail_lines`` lines are
    kept in context, with a middle marker pointing to the saved file. This
    keeps the agent's context bounded without discarding any information and
    requires no LLM call.
    """
    if text is None:
        return text, None

    lines = text.split("\n")
    if len(text) <= max_chars and len(lines) <= max_lines:
        return text, None

    # Persist the complete output for later retrieval via read_file.
    fd, path = tempfile.mkstemp(prefix=f"{tool_name}_output_", suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)

    # lines[-0:] is the whole list in Python; treat 0 as "keep no tail".
    head_n = max(0, head_lines)
    tail_n = max(0, tail_lines)
    head_part = lines[:head_n] if head_n else []
    tail_part = lines[-tail_n:] if tail_n else []
    omitted = max(len(lines) - head_n - tail_n, 0)

    guide = f"[如需完整输出，请使用 read_file 工具读取 {path}]"
    if omitted == 0:
        # Head+tail cover the file; do not concatenate overlapping slices.
        truncated = "\n".join(lines + [guide])
    else:
        middle = f"... [省略 {omitted} 行，完整输出已保存至 {path}] ..."
        truncated = "\n".join(head_part + [middle] + tail_part + [guide])
    return truncated, path


class ExecutionTools:
    """Generic execution tools with safety and result analysis."""
    
    def __init__(self, llm_helper: LLMHelper):
        """Initialize execution tools with LLM helper."""
        self.llm_helper = llm_helper
        self.lang_executor = LanguageExecutor(workspace_dir=Config.WORKSPACE_DIR)
    
    async def code_interpreter(
        self,
        code: str,
        language: str = "python",
        timeout: float = 30.0,
        stdin: Optional[str] = None,
        files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute code in a sandboxed environment with multi-language support.
        
        Args:
            code: Code to execute
            language: Programming language (python, javascript, typescript, go, java, cpp, rust, php, bash)
            timeout: Execution timeout in seconds
            stdin: Optional stdin input
            files: Optional additional files
            
        Returns:
            Result dictionary with output and analysis
        """
        if language is None:
            language = "python"
        language = language.lower()
        
        # Verify syntax first (only for Python for now)
        if Config.AUTO_VERIFY_CODE and language in ['python', 'python3']:
            is_valid, error_msg = self.llm_helper.verify_code_syntax(code, language)
            if not is_valid:
                return {
                    "success": False,
                    "error": f"Syntax error: {error_msg}",
                    "verification": "failed",
                    "language": language
                }
        
        # Check for dangerous operations
        if Config.REQUIRE_APPROVAL_FOR_DANGEROUS_OPS:
            dangerous_patterns = {
                'python': ['os.system', 'subprocess', 'eval', 'exec', 'open(', '__import__', 'compile'],
                'bash': ['rm -rf', 'dd if=', 'mkfs', '> /dev/', 'curl', 'wget'],
                'php': ['exec(', 'system(', 'shell_exec(', 'passthru(', 'eval('],
            }
            
            patterns = dangerous_patterns.get(language, [])
            detected = [p for p in patterns if p in code]
            
            if detected:
                approved, reason = self.llm_helper.request_approval(
                    "code_execution",
                    {
                        "code": code,
                        "language": language,
                        "detected_patterns": detected
                    }
                )
                
                if not approved:
                    return {
                        "success": False,
                        "error": f"Execution not approved: {reason}",
                        "language": language
                    }
        
        # Execute code using multi-language executor
        try:
            result = await self.lang_executor.execute_code(
                code=code,
                language=language,
                timeout=timeout,
                stdin=stdin,
                files=files
            )
            
            # Convert status to success flag
            success = result.get('status') == ExecutionStatus.SUCCESS
            
            # Long outputs: truncate head/tail and persist the full text to a
            # temp file (offline-safe), then optionally LLM-summarize whatever
            # still exceeds the char threshold.
            stdout = result.get('stdout', '')
            stderr = result.get('stderr', '')
            stdout, stdout_file = truncate_and_persist(stdout, "code_interpreter")
            stderr, stderr_file = truncate_and_persist(stderr, "code_interpreter")

            if Config.AUTO_SUMMARIZE_COMPLEX_OUTPUT and len(stdout) > MAX_OUTPUT_CHARS:
                stdout = self.llm_helper.summarize_output("code_interpreter", stdout)
            if Config.AUTO_SUMMARIZE_COMPLEX_OUTPUT and len(stderr) > MAX_OUTPUT_CHARS:
                stderr = self.llm_helper.summarize_output("code_interpreter", stderr)

            return {
                "success": success,
                "status": result.get('status'),
                "language": result.get('language', language),
                "stdout": stdout,
                "stderr": stderr,
                "stdout_file": stdout_file,
                "stderr_file": stderr_file,
                "returncode": result.get('returncode'),
                "error": result.get('error'),
                "compile_output": result.get('compile_output'),
                "phase": result.get('phase'),
                "verification": "passed" if Config.AUTO_VERIFY_CODE else "skipped"
            }
            
        except Exception as e:
            error_output = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
            return {
                "success": False,
                "error": error_output,
                "language": language
            }
    
    async def virtual_terminal(
        self,
        command: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute shell command in a virtual terminal.
        
        Args:
            command: Shell command to execute
            timeout: Timeout in seconds
            
        Returns:
            Result dictionary with output and analysis
        """
        # Check for dangerous commands
        if Config.REQUIRE_APPROVAL_FOR_DANGEROUS_OPS:
            dangerous_commands = [
                'rm -rf', 'dd', 'mkfs', 'format',
                '> /dev/', 'chmod -R', 'chown -R'
            ]
            
            if any(dangerous in command for dangerous in dangerous_commands):
                approved, reason = self.llm_helper.request_approval(
                    "terminal_command",
                    {
                        "command": command,
                        "detected_patterns": [p for p in dangerous_commands if p in command]
                    }
                )
                
                if not approved:
                    return {
                        "success": False,
                        "error": f"Command execution not approved: {reason}"
                    }
        
        # Execute command
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Config.WORKSPACE_DIR
            )
            
            stdout = result.stdout
            stderr = result.stderr

            # Long output: truncate head/tail and persist to a temp file, then
            # optionally LLM-summarize whatever still exceeds the char threshold.
            stdout, stdout_file = truncate_and_persist(stdout, "virtual_terminal")
            stderr, stderr_file = truncate_and_persist(stderr, "virtual_terminal")

            if Config.AUTO_SUMMARIZE_COMPLEX_OUTPUT:
                if len(stdout) > MAX_OUTPUT_CHARS:
                    stdout = self.llm_helper.summarize_output(
                        "virtual_terminal",
                        stdout
                    )
                if len(stderr) > MAX_OUTPUT_CHARS:
                    stderr = self.llm_helper.summarize_output(
                        "virtual_terminal",
                        stderr
                    )

            response = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "stdout_file": stdout_file,
                "stderr_file": stderr_file
            }
            return response
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Command execution failed: {str(e)}"
            }
