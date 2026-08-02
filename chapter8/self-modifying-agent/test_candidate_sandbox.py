import unittest
from unittest.mock import patch

from candidate_sandbox import MAX_SOURCE_BYTES, SandboxError, _docker_command, run_in_sandbox


class CandidateSandboxConfigurationTest(unittest.TestCase):
    def test_docker_command_enforces_isolation_and_resource_limits(self):
        command = _docker_command("sandbox:test", "candidate-test")
        rendered = " ".join(command)
        for expected in (
            "--network none",
            "--ipc none",
            "--read-only",
            "--cap-drop ALL",
            "--security-opt no-new-privileges:true",
            "--user 65534:65534",
            "--pids-limit 16",
            "--memory 64m",
            "--memory-swap 64m",
            "--cpus 0.5",
            "--ulimit cpu=2:2",
            "--log-driver none",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, rendered)
        self.assertNotIn("--volume", command)
        self.assertNotIn("--mount", command)

    def test_oversized_source_is_rejected_before_docker_starts(self):
        with patch("candidate_sandbox._ensure_image") as ensure_image:
            with self.assertRaisesRegex(SandboxError, "exceeds 256 KiB"):
                run_in_sandbox("validate", "x" * (MAX_SOURCE_BYTES + 1), [])
        ensure_image.assert_not_called()

    def test_malformed_unicode_is_rejected_before_docker_starts(self):
        with patch("candidate_sandbox._ensure_image") as ensure_image:
            with self.assertRaisesRegex(SandboxError, "not valid JSON data"):
                run_in_sandbox("validate", "\ud800", [])
        ensure_image.assert_not_called()


if __name__ == "__main__":
    unittest.main()
