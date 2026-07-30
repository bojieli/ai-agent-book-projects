import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from validate_evidence import validate


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name("evidence.blocked.example.json")
        self.blocked = json.loads(path.read_text(encoding="utf-8"))

    def test_honest_blocker_passes(self):
        self.assertEqual(validate(self.blocked), [])

    def test_gpu_only_work_cannot_claim_full_completion(self):
        claim = copy.deepcopy(self.blocked)
        claim["status"] = "complete"
        claim["blockers"] = []
        errors = validate(claim)
        self.assertTrue(any("all five stages" in error for error in errors))
        self.assertTrue(any("actuation authorization" in error for error in errors))

    def test_stage_4_is_not_labeled_hardware_actuation(self):
        claim = copy.deepcopy(self.blocked)
        claim["stages"][3]["robot_actuation_required"] = True
        self.assertTrue(any("stage 4: wrong hardware boundary" in error for error in validate(claim)))

    def test_host_pipeline_executes_without_actuation(self):
        upstream = Path("/tmp/lerobot-sim2real-audit-20260729")
        if not upstream.exists():
            self.skipTest("pinned audit checkout is unavailable")
        runner = Path(__file__).with_name("pipeline.py")
        result = subprocess.run(
            [sys.executable, str(runner), "--upstream", str(upstream)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["actuation_attempted"])
        self.assertEqual(report["stages"]["3"]["real_dynamics_measurement"]["samples"], 139)
        self.assertFalse(report["stages"]["4"]["complete"])


if __name__ == "__main__":
    unittest.main()
