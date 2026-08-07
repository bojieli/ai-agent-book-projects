import unittest

from calibration import calibration_report
from verifier import DimensionResult


class TestCalibrationReportDimensionResult(unittest.TestCase):
    def test_calibration_report_supports_dimension_result_objects(self):
        """Contract: calibration_report handles report dimensions containing DimensionResult objects.

        Locks out TypeError when report dimensions are DimensionResult dataclasses instead of dicts.
        """
        trajectory = {
            "id": "t1",
            "expert_labels": {"task_resolution": "pass"},
        }
        report = {
            "trajectory_id": "t1",
            "dimensions": [
                DimensionResult("task_resolution", "environment_result", "pass", 1.0, ["ok"], 1.0)
            ],
        }
        result = calibration_report([trajectory], [report])
        self.assertEqual(1.0, result["exact_label_agreement"])
        self.assertIn("task_resolution", result["per_dimension"])


if __name__ == "__main__":
    unittest.main()
