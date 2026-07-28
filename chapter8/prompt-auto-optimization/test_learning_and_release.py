import unittest

from learning_signal import diagnose_failures, format_learning_signal
from release_gate import build_candidate_manifest, evaluate_release_gate


def evaluation(holdout=(2, 2), boundary=(0, 2)):
    return {
        "holdout": holdout,
        "boundary": boundary,
        "results": [
            {
                "id": "B1",
                "group": "boundary",
                "correct": False,
                "transferred": True,
                "should_transfer": False,
                "handled": None,
                "note": "不应转接：却转接了",
            }
        ],
    }


class LearningAndReleaseTest(unittest.TestCase):
    def test_diagnosis_comes_from_failed_case(self):
        report = diagnose_failures(evaluation())
        self.assertEqual(["B1"], report["source_case_ids"])
        self.assertEqual("system_prompt.transfer_policy", report["scope"])
        self.assertEqual("B1", report["dimensions"]["compliant_flexibility"][0]["case_id"])
        self.assertIn("Source cases: B1", format_learning_signal(report))

    def test_release_requires_improvement_and_no_regression(self):
        signal = diagnose_failures(evaluation())
        manifest = build_candidate_manifest({"diff": "+ new rule", "rationale": "narrow transfer"}, signal)
        accepted = evaluate_release_gate(evaluation(), evaluation(boundary=(1, 2)), manifest)
        self.assertTrue(accepted["accepted"])
        self.assertEqual("release_to_canary", accepted["decision"])

        regressed = evaluate_release_gate(
            evaluation(holdout=(2, 2)), evaluation(holdout=(1, 2), boundary=(1, 2)), manifest
        )
        self.assertFalse(regressed["accepted"])
        self.assertFalse(regressed["checks"]["holdout_did_not_regress"])

    def test_empty_patch_is_rejected(self):
        signal = diagnose_failures(evaluation())
        manifest = build_candidate_manifest({"diff": "", "rationale": "none"}, signal)
        decision = evaluate_release_gate(evaluation(), evaluation(boundary=(1, 2)), manifest)
        self.assertEqual("reject_candidate", decision["decision"])


if __name__ == "__main__":
    unittest.main()
