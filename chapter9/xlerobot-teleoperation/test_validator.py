import json
import subprocess
import sys
import unittest
from pathlib import Path

from validate_evidence import validate


class EvidenceGateTests(unittest.TestCase):
    def test_local_gpu_evidence_is_accepted(self):
        run = Path(__file__).parent / "validation" / "runs" / "local-gpu" / "evidence.json"
        if not run.is_file():
            self.skipTest("run the local GPU experiment first")
        data = json.loads(run.read_text(encoding="utf-8"))
        self.assertEqual(validate(data, run.parent), [])

    def test_cpu_claim_is_rejected(self):
        data = {
            "schema_version": "3.0",
            "experiment_id": "9-8",
            "status": "complete",
            "kind": "local_gpu_expert_upper_bound",
            "metrics": {"device": {"device": "cpu"}, "protocol": {"seeds": [1, 2, 3], "object_counts": [1, 2, 3], "total_episodes": 2048}, "cells": [], "worst_cell_success_rate": 1.0, "deterministic_replay": True},
            "artifacts": [],
            "hardware_extension": {"actuation_attempted": False},
        }
        self.assertTrue(validate(data))

    def test_runner_requires_accelerator_by_default(self):
        runner = Path(__file__).with_name("teleop.py")
        result = subprocess.run([sys.executable, str(runner), "--help"], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("local GPU", result.stdout)


if __name__ == "__main__":
    unittest.main()
