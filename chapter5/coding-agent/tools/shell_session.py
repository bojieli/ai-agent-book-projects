"""
Cross-platform shell session management for persistent command execution.
"""

import base64
import os
import queue
import re
import shlex
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TextIO, Tuple


def get_background_log_path(job_id: str) -> str:
    """Return a platform-appropriate path for a background job log."""
    return os.path.join(tempfile.gettempdir(), f"{job_id}.log")


def _get_shell_configuration(platform_name: Optional[str] = None) -> Tuple[str, List[str]]:
    """Return the shell dialect and command for the current platform."""
    platform_name = platform_name or os.name

    if platform_name == "nt":
        # PowerShell is available by default on supported Windows versions and
        # accepts common commands such as `python`, `git`, and `ls`. Prefer the
        # newer cross-platform edition when the user has installed it.
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell:
            return "powershell", [
                powershell,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "-",
            ]

        # COMSPEC is a last-resort fallback for stripped-down Windows images
        # where PowerShell is unavailable.
        return "cmd", [os.environ.get("COMSPEC", "cmd.exe"), "/D", "/Q"]

    bash = shutil.which("bash") or "/bin/bash"
    return "bash", [bash]


@dataclass
class ShellSession:
    """Manage a persistent native shell session."""

    session_id: str
    process: Optional[subprocess.Popen] = None
    current_directory: str = field(default_factory=os.getcwd)
    env: Dict[str, str] = field(default_factory=lambda: os.environ.copy())
    output_buffer: str = ""
    shell_kind: str = field(default="", init=False)
    shell_command: List[str] = field(default_factory=list, init=False, repr=False)
    background_processes: Dict[str, subprocess.Popen] = field(
        default_factory=dict, init=False, repr=False
    )

    def _configure_shell(self) -> None:
        if not self.shell_command:
            self.shell_kind, self.shell_command = _get_shell_configuration()

    def start(self) -> None:
        """Start the persistent shell process."""
        if self.process is None or self.process.poll() is not None:
            self._configure_shell()
            self.process = subprocess.Popen(
                self.shell_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=self.current_directory,
                env=self.env,
            )
            # Reader thread feeds stdout lines into a queue so that execute()
            # can wait on them with a real timeout (a bare readline() would
            # block forever on silent commands like `sleep`).
            self._output_queue = queue.Queue()
            reader = threading.Thread(
                target=self._read_stdout,
                args=(self.process, self._output_queue),
                daemon=True,
            )
            reader.start()

    @staticmethod
    def _read_stdout(process: subprocess.Popen, output_queue: queue.Queue) -> None:
        """Pump stdout lines into the queue; None marks end of stream."""
        for line in iter(process.stdout.readline, ""):
            output_queue.put(line)
        output_queue.put(None)

    @staticmethod
    def _quote_powershell(value: str) -> str:
        """Quote a string as a PowerShell single-quoted literal."""
        return "'" + value.replace("'", "''") + "'"

    def _build_command_script(
        self,
        command: str,
        done_marker: str,
        cwd_marker: str,
        env_start_marker: str = "",
        env_end_marker: str = "",
    ) -> str:
        """Wrap a command with platform-specific completion markers."""
        if self.shell_kind == "powershell":
            cwd = self._quote_powershell(self.current_directory)
            # Capture status inside the generated script block immediately
            # after the user's final statement. Checking `$?` after invoking a
            # script block can incorrectly turn command-not-found into success.
            command_with_status = (
                f"{command}\n"
                "$global:__agent_command_succeeded = $?\n"
                "$global:__agent_native_exit_code = $LASTEXITCODE"
            )
            encoded_command = base64.b64encode(
                command_with_status.encode("utf-8")
            ).decode("ascii")
            return (
                "[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
                "$OutputEncoding = [Console]::OutputEncoding; "
                f"Set-Location -LiteralPath {cwd}; "
                "$global:LASTEXITCODE = $null; "
                "$global:__agent_command_succeeded = $false; "
                "$global:__agent_native_exit_code = $null; "
                "$__agent_command = [Text.Encoding]::UTF8.GetString("
                f"[Convert]::FromBase64String('{encoded_command}')); "
                "& ([ScriptBlock]::Create($__agent_command)); "
                "$__agent_exit_code = $global:__agent_native_exit_code; "
                "if ($null -eq $__agent_exit_code) { "
                "  if ($global:__agent_command_succeeded) { $__agent_exit_code = 0 } "
                "else { $__agent_exit_code = 1 } "
                "}; "
                f"Write-Output ('{done_marker}' + $__agent_exit_code); "
                f"Write-Output '{env_start_marker}'; "
                "Get-ChildItem Env: | ForEach-Object { "
                "Write-Output ($_.Name + '=' + $_.Value) }; "
                f"Write-Output '{env_end_marker}'; "
                f"Write-Output ('{cwd_marker}' + (Get-Location).Path)\n"
            )

        if self.shell_kind == "cmd":
            # Double quotes are sufficient for normal Windows paths. A quote
            # cannot occur in a Windows file or directory name.
            cwd = f'"{self.current_directory}"'
            return (
                "chcp 65001 > nul\n"
                f"cd /d {cwd}\n"
                f"{command}\n"
                'set "__agent_exit_code=%errorlevel%"\n'
                f"echo {done_marker}%__agent_exit_code%\n"
                f"echo {env_start_marker}\n"
                "set\n"
                f"echo {env_end_marker}\n"
                f"echo {cwd_marker}%CD%\n"
            )

        cwd = shlex.quote(self.current_directory)
        return (
            f"cd {cwd}\n"
            "{\n"
            f"{command}\n"
            "}\n"
            "__agent_exit_code=$?\n"
            f"printf '%s%s\\n' '{done_marker}' \"$__agent_exit_code\"\n"
            f"printf '%s%s\\n' '{cwd_marker}' \"$PWD\"\n"
        )

    def _parse_protocol_output(
        self,
        output_lines: List[str],
        done_marker: str,
        cwd_marker: str,
        env_start_marker: str = "",
        env_end_marker: str = "",
        fallback_exit_code: int = -1,
    ) -> Tuple[str, int]:
        """Remove internal markers and apply shell state from command output."""
        command_output = []
        environment_lines = []
        reading_environment = False
        exit_code = fallback_exit_code

        for line in output_lines:
            stripped = line.rstrip("\r\n")
            match = re.fullmatch(re.escape(done_marker) + r"(-?\d+)", stripped)
            if match:
                exit_code = int(match.group(1))
                continue

            if env_start_marker and stripped == env_start_marker:
                reading_environment = True
                continue
            if env_end_marker and stripped == env_end_marker:
                reading_environment = False
                updated_environment = {}
                for entry in environment_lines:
                    name, separator, value = entry.partition("=")
                    if separator and name:
                        updated_environment[name] = value
                if updated_environment:
                    self.env = updated_environment
                continue
            if reading_environment:
                environment_lines.append(stripped)
                continue

            if stripped.startswith(cwd_marker) and exit_code != -1:
                new_directory = stripped[len(cwd_marker):]
                if new_directory and os.path.isdir(new_directory):
                    self.current_directory = new_directory
                continue

            command_output.append(stripped)

        return "\n".join(command_output), exit_code

    def _restart(self) -> None:
        """Replace a stuck shell while retaining session state."""
        self._terminate_process(self.process)
        self.process = None
        self.start()

    @staticmethod
    def _terminate_process(process: Optional[subprocess.Popen]) -> None:
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    def execute(self, command: str, timeout: float = 120) -> Tuple[str, int]:
        """Execute a command in the persistent native shell."""
        self._configure_shell()

        # PowerShell and cmd read redirected stdin through end-of-file rather
        # than executing it incrementally. Run one process per Windows command
        # and carry its directory/environment forward to preserve session state.
        if self.shell_kind in {"powershell", "cmd"}:
            return self._execute_windows(command, timeout)

        self.start()

        try:
            # A per-command nonce prevents command output that happens to look
            # like a protocol marker from truncating or desynchronizing output.
            nonce = uuid.uuid4().hex
            done_marker = f"__CMD_DONE_{nonce}__"
            cwd_marker = f"__CMD_CWD_{nonce}__"
            script = self._build_command_script(command, done_marker, cwd_marker)

            self.process.stdin.write(script)
            self.process.stdin.flush()

            output_lines = []
            deadline = time.monotonic() + timeout

            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    # Replace the stuck shell so its pending marker cannot
                    # corrupt output from the next command.
                    self._restart()
                    return f"Command timed out (timeout: {timeout}s)", -1

                try:
                    line = self._output_queue.get(timeout=remaining)
                except queue.Empty:
                    self._restart()
                    return f"Command timed out (timeout: {timeout}s)", -1

                if line is None:  # shell exited unexpectedly
                    break

                stripped = line.rstrip("\r\n")
                output_lines.append(stripped)
                if stripped.startswith(cwd_marker):
                    break

            return self._parse_protocol_output(
                output_lines,
                done_marker,
                cwd_marker,
            )

        except Exception as exc:
            return f"Error executing command: {exc}", -1

    def _execute_windows(self, command: str, timeout: float) -> Tuple[str, int]:
        """Execute one Windows command while preserving logical session state."""
        nonce = uuid.uuid4().hex
        done_marker = f"__CMD_DONE_{nonce}__"
        cwd_marker = f"__CMD_CWD_{nonce}__"
        env_start_marker = f"__CMD_ENV_START_{nonce}__"
        env_end_marker = f"__CMD_ENV_END_{nonce}__"
        script = self._build_command_script(
            command,
            done_marker,
            cwd_marker,
            env_start_marker,
            env_end_marker,
        )

        process = subprocess.Popen(
            self.shell_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=self.current_directory,
            env=self.env,
        )
        try:
            output, _ = process.communicate(script, timeout=timeout)
        except subprocess.TimeoutExpired:
            self._terminate_process(process)
            return f"Command timed out (timeout: {timeout}s)", -1
        except Exception:
            self._terminate_process(process)
            raise

        return self._parse_protocol_output(
            output.splitlines(),
            done_marker,
            cwd_marker,
            env_start_marker,
            env_end_marker,
            fallback_exit_code=process.returncode,
        )

    def _background_shell_command(self, command: str) -> List[str]:
        """Build a one-shot shell command for a background process."""
        self._configure_shell()
        executable = self.shell_command[0]

        if self.shell_kind == "powershell":
            encoded_command = base64.b64encode(
                (
                    "[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
                    "$OutputEncoding = [Console]::OutputEncoding; "
                    + command
                ).encode("utf-16-le")
            ).decode("ascii")
            return [
                executable,
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                encoded_command,
            ]
        if self.shell_kind == "cmd":
            return [executable, "/D", "/S", "/C", f"chcp 65001 > nul & {command}"]
        return [executable, "-c", command]

    def start_background(self, command: str, job_id: str) -> int:
        """Start a command in a separate process and log combined output."""
        log_path = get_background_log_path(job_id)

        # Keep POSIX background jobs in the persistent Bash process so exports
        # made by earlier commands remain visible, matching the original tool
        # behavior. Windows commands use one-shot native shell processes.
        self._configure_shell()
        if self.shell_kind == "bash":
            background_command = (
                f"( {command} ) > {shlex.quote(log_path)} 2>&1 & echo $!"
            )
            output, exit_code = self.execute(background_command, timeout=5)
            if exit_code != 0:
                raise RuntimeError(f"Unable to start background command: {output}")
            try:
                return int(output.strip().splitlines()[-1])
            except (IndexError, ValueError) as exc:
                raise RuntimeError(
                    f"Unable to determine background command PID: {output}"
                ) from exc

        log_handle = open(log_path, "w", encoding="utf-8")
        try:
            process = subprocess.Popen(
                self._background_shell_command(command),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                cwd=self.current_directory,
                env=self.env,
                text=True,
            )
        except Exception:
            log_handle.close()
            try:
                os.remove(log_path)
            except OSError:
                pass
            raise

        self.background_processes[job_id] = process
        closer = threading.Thread(
            target=self._close_log_when_done,
            args=(process, log_handle),
            daemon=True,
        )
        closer.start()
        return process.pid

    @staticmethod
    def _close_log_when_done(process: subprocess.Popen, log_handle: TextIO) -> None:
        process.wait()
        log_handle.close()

    def kill(self) -> None:
        """Terminate the persistent shell and its background processes."""
        self._terminate_process(self.process)
        for process in list(self.background_processes.values()):
            self._terminate_process(process)
