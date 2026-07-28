import json
import unittest
from pathlib import Path

from calibration import calibration_report
from verifier import TrajectoryVerifier, diagnostic_utility, scalar_baseline


class VerifierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).with_name("sample_trajectories.json")
        cls.trajectories = json.loads(path.read_text(encoding="utf-8"))
        cls.reports = [TrajectoryVerifier().evaluate(item) for item in cls.trajectories]

    def test_false_promise_has_evidence(self):
        report = self.reports[1]
        failed = {item["dimension"]: item for item in report["dimensions"] if item["verdict"] == "fail"}
        self.assertIn("promise_action_consistency", failed)
        self.assertTrue(failed["promise_action_consistency"]["evidence"])
        self.assertEqual("reject", report["release_recommendation"])

    def test_multidimensional_report_is_more_diagnostic_than_scalar(self):
        report = self.reports[1]
        self.assertEqual({"trajectory_id", "score"}, set(scalar_baseline(report)))
        self.assertEqual(1.0, diagnostic_utility(report))

    def test_calibration_matches_experts(self):
        calibration = calibration_report(self.trajectories, self.reports)
        self.assertEqual(1.0, calibration["exact_label_agreement"])


if __name__ == "__main__":
    unittest.main()
