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

    def test_renaming_blocker_to_complete_fails_closed(self):
        claim = copy.deepcopy(self.blocked)
        claim["status"] = "complete"
        claim["blockers"] = []
        errors = validate(claim)
        self.assertTrue(errors)
        self.assertTrue(any("actuation authorization" in error for error in errors))

    def test_launcher_defaults_to_dry_config(self):
        runner = Path(__file__).with_name("teleop.py")
        upstream = Path("/tmp/xlerobot-audit-20260729")
        if not upstream.exists():
            self.skipTest("pinned audit checkout is unavailable")
        result = subprocess.run(
            [sys.executable, str(runner), "--upstream", str(upstream), "--mode", "keyboard"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("DRY CONFIG ONLY", result.stdout)


if __name__ == "__main__":
    unittest.main()
