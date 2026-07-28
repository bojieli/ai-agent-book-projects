"""Multi-language code execution support inspired by SandboxFusion."""

import asyncio
import subprocess
import tempfile
import os
import shutil
import time
import base64
import psutil
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


def try_decode(s: bytes) -> str:
    """Safely decode bytes to string."""
    try:
        return s.decode('utf-8', errors='replace')
    except Exception as e:
        return f'[DecodeError] {e}'


async def get_all_output(stream) -> str:
    """Read stream until EOF. Call after the process has exited or been killed."""
    if stream is None:
        return ""
    try:
        result = await stream.read()
        return try_decode(result)
    except Exception as e:
        logger.debug(f"Error reading output: {e}")
        return ""


def kill_process_tree(pid: int):
    """Kill process and all its children."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Kill children first
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        
        # Kill parent
        try:
            parent.kill()
        except psutil.NoSuchProcess:
            pass
            
    except psutil.NoSuchProcess:
        pass
    except Exception as e:
        logger.warning(f'Error killing process tree: {e}')


class ExecutionStatus(str, Enum):
    """Execution status."""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    ERROR = "error"


class LanguageExecutor:
    """Multi-language code executor."""
    
    def __init__(self, workspace_dir: str = None):
        """Initialize executor."""
        self.workspace_dir = workspace_dir or os.getcwd()
    
    async def execute_code(
        self,
        code: str,
        language: str,
        timeout: float = 30.0,
        compile_timeout: float = 10.0,
        stdin: Optional[str] = None,
        files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute code in the specified language.
        
        Args:
            code: Code to execute
            language: Programming language
            timeout: Execution timeout in seconds
            compile_timeout: Compilation timeout in seconds
            stdin: Optional stdin input
            files: Optional additional files (name -> content)
            
        Returns:
            Execution result dictionary
        """
        if language is None:
            language = "python"
        language = language.lower()
        
        # Map language to executor
        executors = {
            'python': self._run_python,
            'python3': self._run_python,
            'javascript': self._run_javascript,
            'js': self._run_javascript,
            'typescript': self._run_typescript,
            'ts': self._run_typescript,
            'go': self._run_go,
            'java': self._run_java,
            'cpp': self._run_cpp,
            'c++': self._run_cpp,
            'rust': self._run_rust,
            'php': self._run_php,
            'bash': self._run_bash,
            'shell': self._run_bash,
            'sh': self._run_bash,
            'nodejs': self._run_javascript,
            'node': self._run_javascript,
        }
        
        executor = executors.get(language)
        if not executor:
            return {
                "status": ExecutionStatus.ERROR,
                "error": f"Unsupported language: {language}. Supported: {', '.join(sorted(set(executors.keys())))}"
            }
        
        try:
            return await executor(code, timeout, compile_timeout, stdin, files or {})
        except Exception as e:
            logger.exception(f"Error executing {language} code")
            return {
                "status": ExecutionStatus.ERROR,
                "error": f"Execution failed: {str(e)}"
            }
    
    async def _run_command(
        self,
        command: str,
        timeout: float,
        stdin: Optional[str] = None,
        cwd: Optional[str] = None,
        shell: bool = True
    ) -> Dict[str, Any]:
        """Run a shell command and return results with proper process management."""
        process = None
        try:
            logger.debug(f'Running command: {command[:100]}...')
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdin=asyncio.subprocess.PIPE if stdin else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                executable='/bin/bash'
            )
            
            # Write stdin if provided
            if stdin and process.stdin:
                try:
                    process.stdin.write(stdin.encode())
                    await process.stdin.drain()
                    process.stdin.close()
                except Exception as e:
                    logger.warning(f"Failed to write stdin: {e}")
            
            start_time = time.time()

            # Drain both pipes concurrently with the wait. Reading only *after*
            # process.wait() deadlocks as soon as the child fills the OS pipe
            # buffer (~256 KB here): the child blocks in write(), so it never
            # exits and wait() never returns, turning a fast program with large
            # stdout into a bogus TIMEOUT.
            stdout_task = asyncio.ensure_future(get_all_output(process.stdout))
            stderr_task = asyncio.ensure_future(get_all_output(process.stderr))

            try:
                # Wait for process with timeout
                await asyncio.wait_for(process.wait(), timeout=timeout)
                execution_time = time.time() - start_time

                stdout = await stdout_task
                stderr = await stderr_task

                logger.debug(f'Command completed in {execution_time:.2f}s')
                
                return {
                    "status": ExecutionStatus.SUCCESS if process.returncode == 0 else ExecutionStatus.FAILED,
                    "returncode": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "execution_time": execution_time
                }
                
            except asyncio.TimeoutError:
                execution_time = time.time() - start_time

                # Kill first so pipes close, then drain remaining output
                if psutil.pid_exists(process.pid):
                    kill_process_tree(process.pid)
                    logger.info(f'Process {process.pid} killed due to timeout')

                stdout = await stdout_task
                stderr = await stderr_task
                
                return {
                    "status": ExecutionStatus.TIMEOUT,
                    "error": f"Execution timed out after {timeout} seconds",
                    "stdout": stdout,
                    "stderr": stderr,
                    "execution_time": execution_time
                }
                
        except Exception as e:
            logger.exception(f"Error running command: {command[:100]}")
            return {
                "status": ExecutionStatus.ERROR,
                "error": f"Command execution failed: {str(e)}"
            }
        finally:
            # Cleanup: ensure process is terminated
            if process and psutil.pid_exists(process.pid):
                kill_process_tree(process.pid)
    
    def _write_files(self, tmp_dir: str, files: Dict[str, str]):
        """Write additional files to tmp directory."""
        for filename, content in files.items():
            if not content or "IGNORE_THIS_FILE" in filename:
                continue
                
            filepath = os.path.join(tmp_dir, filename)
            dirpath = os.path.dirname(filepath)
            
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)
            
            # Handle base64 encoded content
            try:
                if self._is_base64(content):
                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(content))
                else:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
            except Exception as e:
                logger.warning(f"Failed to write file {filename}: {e}")
    
    def _is_base64(self, s: str) -> bool:
        """Check if string is base64 encoded."""
        try:
            if len(s) % 4 != 0 or not all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in s):
                return False
            base64.b64decode(s, validate=True)
            return True
        except Exception:
            return False
    
    async def _run_python(
        self,
        code: str,
        timeout: float,
        compile_timeout: float,
        stdin: Optional[str],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute Python code."""
        with tempfile.TemporaryDirectory(prefix='python_', ignore_cleanup_errors=True) as tmp_dir:
            self._write_files(tmp_dir, files)
            code_file = os.path.join(tmp_dir, 'main.py')
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Use python3 with unbuffered output
            result = await self._run_command(
                f'python3 -u {code_file}',
                timeout,
                stdin,
                tmp_dir
            )
            result['language'] = 'python'
            return result
    
    async def _run_javascript(
        self,
        code: str,
        timeout: float,
        compile_timeout: float,
        stdin: Optional[str],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute JavaScript code with Node.js."""
        with tempfile.TemporaryDirectory(prefix='js_', ignore_cleanup_errors=True) as tmp_dir:
            self._write_files(tmp_dir, files)
            
            # Create package.json if not exists to enable ES modules
            if 'package.json' not in files:
                package_json = {
                    "type": "module",
                    "dependencies": {}
                }
                with open(os.path.join(tmp_dir, 'package.json'), 'w') as f:
                    import json
                    json.dump(package_json, f)
            
            code_file = os.path.join(tmp_dir, 'main.js')
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            result = await self._run_command(
                f'node {code_file}',
                timeout,
                stdin,
                tmp_dir
            )
            result['language'] = 'javascript'
            return result
    
    async def _run_typescript(
        self,
        code: str,
        timeout: float,
        compile_timeout: float,
        stdin: Optional[str],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute TypeScript code with tsx."""
        with tempfile.TemporaryDirectory(prefix='ts_', ignore_cleanup_errors=True) as tmp_dir:
            self._write_files(tmp_dir, files)
            code_file = os.path.join(tmp_dir, 'main.ts')
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Check if tsx is available, fallback to ts-node
            check_tsx = await self._run_command('which tsx 2>/dev/null', 1.0)
            cmd = 'tsx' if check_tsx['status'] == ExecutionStatus.SUCCESS else 'ts-node'
            
            result = await self._run_command(
                f'{cmd} {code_file}',
                timeout,
                stdin,
                tmp_dir
            )
            result['language'] = 'typescript'
            return result
    
    async def _run_go(
        self,
        code: str,
        timeout: float,
        compile_timeout: float,
        stdin: Optional[str],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute Go code."""
        with tempfile.TemporaryDirectory(prefix='go_', ignore_cleanup_errors=True) as tmp_dir:
            self._write_files(tmp_dir, files)
            
            # Initialize go module (ignore errors if already exists)
            await self._run_command('go mod init main 2>/dev/null || true', 2.0, cwd=tmp_dir)
            
            code_file = os.path.join(tmp_dir, 'main.go')
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Compile
            compile_result = await self._run_command(
                'go build -o main main.go',
                compile_timeout,
                cwd=tmp_dir
            )
            
            if compile_result['status'] != ExecutionStatus.SUCCESS:
                return {
                    "status": ExecutionStatus.FAILED,
                    "language": "go",
                    "phase": "compilation",
                    "returncode": compile_result.get('returncode', 1),
                    "stdout": compile_result.get('stdout', ''),
                    "stderr": compile_result.get('stderr', ''),
                    "error": "Compilation failed"
                }
            
            # Run
            result = await self._run_command(
                './main',
                timeout,
                stdin,
                tmp_dir
            )
            result['language'] = 'go'
            result['compile_stdout'] = compile_result.get('stdout', '')
            result['compile_stderr'] = compile_result.get('stderr', '')
            return result
    
    async def _run_java(
        self,
        code: str,
        timeout: float,
        compile_timeout: float,
        stdin: Optional[str],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute Java code."""
        with tempfile.TemporaryDirectory(prefix='java_', ignore_cleanup_errors=True) as tmp_dir:
            self._write_files(tmp_dir, files)
            
            # Extract class name from public class declaration
            class_name = 'Main'
            import re
            match = re.search(r'public\s+class\s+(\w+)', code)
            if match:
                class_name = match.group(1)
            
            code_file = os.path.join(tmp_dir, f'{class_name}.java')
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Prepare classpath for additional jars
            jars = [f for f in files.keys() if f.endswith('.jar')]
            classpath = '.:' + ':'.join(jars) if jars else '.'
            
            # Compile
            compile_result = await self._run_command(
                f'javac -cp {classpath} {class_name}.java',
                compile_timeout,
                cwd=tmp_dir
            )
            
            if compile_result['status'] != ExecutionStatus.SUCCESS:
                return {
                    "status": ExecutionStatus.FAILED,
                    "language": "java",
                    "phase": "compilation",
                    "returncode": compile_result.get('returncode', 1),
                    "stdout": compile_result.get('stdout', ''),
                    "stderr": compile_result.get('stderr', ''),
                    "error": "Compilation failed"
                }
            
            # Run with assertions enabled
            result = await self._run_command(
                f'java -cp {classpath} -ea {class_name}',
                timeout,
                stdin,
                tmp_dir
            )
            result['language'] = 'java'
            result['compile_stdout'] = compile_result.get('stdout', '')
            result['compile_stderr'] = compile_result.get('stderr', '')
            return result
    
    async def _run_cpp(
        self,
        code: str,
        timeout: float,
        compile_timeout: float,
        stdin: Optional[str],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute C++ code."""
        with tempfile.TemporaryDirectory(prefix='cpp_', ignore_cleanup_errors=True) as tmp_dir:
            self._write_files(tmp_dir, files)
            code_file = os.path.join(tmp_dir, 'main.cpp')
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Compile with commonly needed flags
            # Try with optional libraries (crypto, ssl, pthread)
            compile_flags = '-std=c++17 -O2'
            optional_libs = []
            
            # Check if we need pthread
            if '#include <thread>' in code or 'std::thread' in code:
                optional_libs.append('-lpthread')
            
            libs = ' '.join(optional_libs)
            compile_result = await self._run_command(
                f'g++ {compile_flags} main.cpp -o main {libs}',
                compile_timeout,
                cwd=tmp_dir
            )
            
            if compile_result['status'] != ExecutionStatus.SUCCESS:
                return {
                    "status": ExecutionStatus.FAILED,
                    "language": "cpp",
                    "phase": "compilation",
                    "returncode": compile_result.get('returncode', 1),
                    "stdout": compile_result.get('stdout', ''),
                    "stderr": compile_result.get('stderr', ''),
                    "error": "Compilation failed"
                }
            
            # Run
            result = await self._run_command(
                './main',
                timeout,
                stdin,
                tmp_dir
            )
            result['language'] = 'cpp'
            result['compile_stdout'] = compile_result.get('stdout', '')
            result['compile_stderr'] = compile_result.get('stderr', '')
            return result
    
    async def _run_rust(
        self,
        code: str,
        timeout: float,
        compile_timeout: float,
        stdin: Optional[str],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute Rust code."""
        with tempfile.TemporaryDirectory(prefix='rust_', ignore_cleanup_errors=True) as tmp_dir:
            self._write_files(tmp_dir, files)
            code_file = os.path.join(tmp_dir, 'main.rs')
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Compile with optimizations
            compile_result = await self._run_command(
                'rustc -O main.rs -o main',
                compile_timeout,
                cwd=tmp_dir
            )
            
            if compile_result['status'] != ExecutionStatus.SUCCESS:
                return {
                    "status": ExecutionStatus.FAILED,
                    "language": "rust",
                    "phase": "compilation",
                    "returncode": compile_result.get('returncode', 1),
                    "stdout": compile_result.get('stdout', ''),
                    "stderr": compile_result.get('stderr', ''),
                    "error": "Compilation failed"
                }
            
            # Run
            result = await self._run_command(
                './main',
                timeout,
                stdin,
                tmp_dir
            )
            result['language'] = 'rust'
            result['compile_stdout'] = compile_result.get('stdout', '')
            result['compile_stderr'] = compile_result.get('stderr', '')
            return result
    
    async def _run_php(
        self,
        code: str,
        timeout: float,
        compile_timeout: float,
        stdin: Optional[str],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute PHP code."""
        with tempfile.TemporaryDirectory(prefix='php_', ignore_cleanup_errors=True) as tmp_dir:
            self._write_files(tmp_dir, files)
            
            # Ensure PHP tags
            code_clean = code.strip()
            if not code_clean.startswith('<?php') and not code_clean.startswith('<?'):
                code = '<?php\n' + code
            
            code_file = os.path.join(tmp_dir, 'main.php')
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            result = await self._run_command(
                f'php -f {code_file}',
                timeout,
                stdin,
                tmp_dir
            )
            result['language'] = 'php'
            return result
    
    async def _run_bash(
        self,
        code: str,
        timeout: float,
        compile_timeout: float,
        stdin: Optional[str],
        files: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute Bash script."""
        with tempfile.TemporaryDirectory(prefix='bash_', ignore_cleanup_errors=True) as tmp_dir:
            self._write_files(tmp_dir, files)
            code_file = os.path.join(tmp_dir, 'script.sh')
            with open(code_file, 'w', encoding='utf-8') as f:
                # Add shebang if not present
                if not code.startswith('#!'):
                    f.write('#!/bin/bash\n')
                f.write(code)
            
            # Make executable
            os.chmod(code_file, 0o755)
            
            result = await self._run_command(
                f'bash {code_file}',
                timeout,
                stdin,
                tmp_dir
            )
            result['language'] = 'bash'
            return result
