import json
import unittest
from pathlib import Path

from evolution import (
    diagnose, generate_candidate, generate_rejected_control,
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


if __name__ == "__main__":
    unittest.main()
