import json
import tempfile
import unittest
from pathlib import Path
import uuid

from evolution import (
    behavior_metrics, diagnose, generate_candidate, generate_rejected_control,
    release_manifest, validate_candidate,
)


ROOT = Path(__file__).parent


class SelfModificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trajectories = json.loads((ROOT / "failure_trajectories.json").read_text(encoding="utf-8"))
        cls.stable = (ROOT / "stable" / "retry_policy.py").read_text(encoding="utf-8")
        cls.diagnosis = diagnose(cls.trajectories)
        cls.candidate = generate_candidate(cls.stable, cls.diagnosis)

    def test_diagnosis_selects_control_code_not_prompt(self):
        self.assertTrue(self.diagnosis["change_required"])
        self.assertEqual("stable/retry_policy.py", self.diagnosis["target"])
        self.assertNotIn("prompt", self.diagnosis["target"])
        self.assertEqual(2, len(self.diagnosis["source_case_ids"]))

    def test_candidate_stops_permanent_error_and_keeps_temporary_retry(self):
        checks = validate_candidate(self.candidate["source"], self.trajectories)
        self.assertTrue(all(checks.values()))
        self.assertIn("if not retryable", self.candidate["source"])
        self.assertIn("PAYMENT_DECLINED", self.candidate["source"])

    def test_behavior_metrics_are_evaluated_in_sandbox(self):
        metrics = behavior_metrics(self.candidate["source"], self.trajectories)
        self.assertEqual(1.0, metrics["mean_nonretryable_calls"])
        self.assertEqual(1.0, metrics["temporary_error_recovery_rate"])
        self.assertEqual(0, metrics["old_task_regressions"])

    def test_release_manifest_keeps_rollback_and_stable_source(self):
        checks = validate_candidate(self.candidate["source"], self.trajectories)
        manifest = release_manifest(self.stable, self.candidate, self.diagnosis, checks)
        self.assertEqual("release_to_canary", manifest["decision"])
        self.assertEqual(manifest["stable_version"], manifest["rollback_version"])
        self.assertIn('VERSION = "1.0.0"', self.stable)

    def test_regression_failure_rejects_candidate(self):
        checks = {"static_compile": True, "failure_replay": True, "old_task_regression": False}
        manifest = release_manifest(self.stable, self.candidate, self.diagnosis, checks)
        self.assertEqual("reject_candidate", manifest["decision"])

    def test_bad_fix_is_retained_with_concrete_rejection_reason(self):
        candidate = generate_rejected_control(self.stable, self.diagnosis)
        checks = validate_candidate(candidate["source"], self.trajectories, self.stable)
        manifest = release_manifest(self.stable, candidate, self.diagnosis, checks)
        self.assertEqual("reject_candidate", manifest["decision"])
        self.assertIn("temporary_recovery", manifest["failed_checks"])
        self.assertTrue(manifest["rejection_reason"])

    def test_manifest_contains_change_contract_canary_and_rollback(self):
        checks = validate_candidate(self.candidate["source"], self.trajectories, self.stable)
        manifest = release_manifest(self.stable, self.candidate, self.diagnosis, checks)
        self.assertTrue(manifest["failure_cluster"])
        self.assertTrue(manifest["source_trajectories"])
        self.assertEqual("retry_and_circuit_breaker_control", manifest["target_component"])
        self.assertTrue(manifest["expected_fix"])
        self.assertTrue(manifest["potential_regressions"])
        self.assertTrue(manifest["canary_gate"]["eligible"])
        self.assertEqual(manifest["stable_sha256"], manifest["rollback_sha256"])

    def test_degenerate_candidate_is_rejected_without_crashing(self):
        # A syntactically valid but degenerate source (e.g. an empty LLM reply)
        # compiles yet defines neither public function; validate_candidate must
        # reject it cleanly, not raise KeyError from the behavior gates.
        for source in ("\n", "# only a comment\n"):
            checks = validate_candidate(source, self.trajectories)
            self.assertFalse(all(checks.values()))
            self.assertFalse(checks["failure_replay"])

        checks = validate_candidate("\ud800", self.trajectories)
        self.assertFalse(all(checks.values()))

    def test_candidate_exception_is_rejected_without_crashing(self):
        source = self.candidate["source"].replace(
            '    """Return whether another tool call should be attempted."""',
            '    raise RuntimeError("candidate failed")',
            1,
        )
        checks = validate_candidate(source, self.trajectories)
        self.assertTrue(checks["public_api_compatible"])
        self.assertFalse(checks["failure_replay"])

    def test_unsafe_candidate_is_not_executed_during_validation(self):
        # The security scan must run before the candidate is exec()'d, so a
        # source flagged unsafe never runs its module-level side effects.
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "marker"
            unsafe = (
                "import pathlib\n"
                f"pathlib.Path({str(marker)!r}).write_text('ran')\n"
                "def should_retry(error_code, retryable, attempt):\n    return False\n"
                "def should_open_circuit(consecutive_failures, *, error_code='', retryable=True):\n"
                "    return True\n"
            )
            checks = validate_candidate(unsafe, self.trajectories)
            self.assertFalse(checks["security_scan"])
            self.assertFalse(marker.exists())

    def test_builtins_open_bypass_is_confined_to_container(self):
        marker = Path(tempfile.gettempdir()) / f"agent-sandbox-{uuid.uuid4().hex}"
        source = (
            f'__builtins__["open"]({str(marker)!r}, "w").write("sandboxed")\n'
            + self.candidate["source"]
        )
        try:
            checks = validate_candidate(source, self.trajectories, self.stable)
            # This intentionally demonstrates why the AST scan is not the boundary.
            self.assertTrue(checks["security_scan"])
            self.assertTrue(checks["sandbox_execution"])
            self.assertTrue(all(checks.values()))
            self.assertFalse(marker.exists())
        finally:
            marker.unlink(missing_ok=True)

    def test_nonterminating_candidate_fails_closed(self):
        checks = validate_candidate("while True:\n    pass\n", self.trajectories)
        self.assertTrue(checks["static_compile"])
        self.assertTrue(checks["security_scan"])
        self.assertFalse(checks["sandbox_execution"])
        self.assertFalse(all(checks.values()))

    def test_candidate_has_no_network_access(self):
        network_probe = (
            '_socket = __builtins__["__import__"]("socket").socket()\n'
            '_network_available = _socket.connect_ex(("1.1.1.1", 53)) == 0\n'
            "_socket.close()\n"
        )
        source = (network_probe + self.candidate["source"]).replace(
            "    if not retryable or error_code in NON_RETRYABLE_CODES:",
            "    if _network_available:\n"
            '        raise RuntimeError("sandbox unexpectedly has network access")\n'
            "    if not retryable or error_code in NON_RETRYABLE_CODES:",
            1,
        )
        checks = validate_candidate(source, self.trajectories, self.stable)
        self.assertTrue(checks["security_scan"])
        self.assertTrue(checks["sandbox_execution"])
        self.assertTrue(all(checks.values()))


if __name__ == "__main__":
    unittest.main()
