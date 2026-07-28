"""
Test cases for ShellSession __CMD_DONE__ marker handling
"""

from unittest.mock import MagicMock, patch

from tools import shell_session
from tools.shell_session import ShellSession


class TestShellSelection:
    """Test platform-specific shell selection and command wrapping."""

    def test_windows_prefers_powershell(self):
        def find_shell(name):
            if name == "powershell":
                return r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
            return None

        with patch.object(shell_session.shutil, "which", side_effect=find_shell):
            kind, command = shell_session._get_shell_configuration("nt")

        assert kind == "powershell"
        assert command[0].endswith("powershell.exe")
        assert command[-2:] == ["-Command", "-"]
        assert "/bin/bash" not in command

    def test_windows_falls_back_to_comspec(self):
        with patch.object(shell_session.shutil, "which", return_value=None):
            with patch.dict(
                shell_session.os.environ,
                {"COMSPEC": r"C:\Windows\System32\cmd.exe"},
            ):
                kind, command = shell_session._get_shell_configuration("nt")

        assert kind == "cmd"
        assert command == [r"C:\Windows\System32\cmd.exe", "/D", "/Q"]

    def test_execute_uses_selected_windows_shell(self):
        process = MagicMock()
        process.communicate.return_value = (
            "hello\n"
            "__CMD_DONE_fixed__0\n"
            "__CMD_ENV_START_fixed__\n"
            "PATH=C:\\Windows\n"
            "__CMD_ENV_END_fixed__\n"
            "__CMD_CWD_fixed__C:\\workspace\n",
            None,
        )
        process.returncode = 0
        windows_command = ["powershell.exe", "-NoLogo", "-Command", "-"]
        session = ShellSession(session_id="test_windows_start")

        with patch.object(
            shell_session,
            "_get_shell_configuration",
            return_value=("powershell", windows_command),
        ):
            with patch.object(shell_session.uuid, "uuid4") as make_uuid:
                make_uuid.return_value.hex = "fixed"
                with patch.object(
                    shell_session.subprocess, "Popen", return_value=process
                ) as popen:
                    output, exit_code = session.execute("Write-Output hello")

        assert session.shell_kind == "powershell"
        assert popen.call_args.args[0] == windows_command
        assert "Set-Location" in process.communicate.call_args.args[0]
        assert output == "hello"
        assert exit_code == 0
        assert session.env == {"PATH": r"C:\Windows"}

    def test_powershell_protocol_quotes_windows_working_directory(self):
        session = ShellSession(
            session_id="test_windows_protocol",
            current_directory=r"C:\Users\O'Brien\coding-agent",
        )
        session.shell_kind = "powershell"

        script = session._build_command_script(
            "python hello_world.py", "__DONE__", "__CWD__"
        )

        assert "Set-Location -LiteralPath 'C:\\Users\\O''Brien\\coding-agent'" in script
        assert "[Convert]::FromBase64String" in script
        assert "Write-Output ('__DONE__' + $__agent_exit_code)" in script
        assert "Write-Output ('__CWD__' + (Get-Location).Path)" in script


class TestShellSessionMarker:
    """Test that command output containing the marker string can't break the protocol"""

    def test_basic_command_and_exit_code(self):
        """Normal commands still work and report exit codes"""
        s = ShellSession(session_id="test_basic")
        try:
            out, code = s.execute("echo hello", timeout=10)
            assert code == 0
            assert "hello" in out
            out, code = s.execute("false", timeout=10)
            assert code == 1
        finally:
            s.kill()

    def test_output_containing_marker_text(self):
        """Output containing the marker text must not crash or be truncated"""
        s = ShellSession(session_id="test_marker_text")
        try:
            out, code = s.execute('echo "prefix__CMD_DONE__notanumber"', timeout=10)
            assert code == 0
            assert "prefix__CMD_DONE__notanumber" in out
        finally:
            s.kill()

    def test_marker_text_does_not_desync_next_command(self):
        """Marker-like output must not swallow the next command's output"""
        s = ShellSession(session_id="test_desync")
        try:
            s.execute('echo "see __CMD_DONE__123 here"', timeout=10)
            out, code = s.execute("echo hello-after", timeout=10)
            assert code == 0
            assert "hello-after" in out
        finally:
            s.kill()

    def test_execute_when_cwd_contains_spaces(self, temp_dir):
        """ShellSession must quote cwd so paths with spaces do not break cd."""
        space_dir = temp_dir / "dir with spaces"
        space_dir.mkdir()
        s = ShellSession(
            session_id="test_cwd_spaces",
            current_directory=str(space_dir),
        )
        try:
            out, code = s.execute("pwd", timeout=10)
            assert code == 0
            assert "dir with spaces" in out
            assert "too many arguments" not in out.lower()
        finally:
            s.kill()
