import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validate_evidence import validate


class EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name("evidence.blocked.example.json")
        self.blocked = json.loads(path.read_text(encoding="utf-8"))

    def test_honest_blocker_passes(self):
        self.assertEqual(validate(self.blocked), [])

    def test_generic_gemini_cannot_pass(self):
        claim = copy.deepcopy(self.blocked)
        claim["status"] = "complete"
        claim["blockers"] = []
        claim["planner"]["model"] = "gemini-3-flash-preview"
        errors = validate(claim)
        self.assertTrue(any("planner model" in error for error in errors))

    def test_runner_defaults_to_non_actuating_config(self):
        runner = Path(__file__).with_name("navigation.py")
        result = subprocess.run([sys.executable, str(runner)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("DRY CONFIG ONLY", result.stdout)
        self.assertIn("gemini-robotics-er-1.5-preview", result.stdout)

    def test_saved_frame_planner_blocks_without_key_but_writes_annotated_input(self):
        from PIL import Image

        runner = Path(__file__).with_name("plan_saved_frame.py")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source, annotated, output = tmp_path / "frame.png", tmp_path / "annotated.png", tmp_path / "plan.json"
            Image.new("RGB", (160, 120), "gray").save(source)
            env = {key: value for key, value in __import__("os").environ.items() if key not in {"GOOGLE_API_KEY", "GEMINI_API_KEY"}}
            result = subprocess.run(
                [sys.executable, str(runner), "--image", str(source), "--annotated-image", str(annotated), "--output", str(output)],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            record = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(record["status"], "blocked")
            self.assertFalse(record["actuation_attempted"])
            self.assertTrue(annotated.is_file())

    def test_preflight_accepts_gemini_alias_without_exposing_value(self):
        upstream = Path("/tmp/xlerobot-audit-20260729")
        if not upstream.exists():
            self.skipTest("pinned audit checkout is unavailable")
        preflight = Path(__file__).with_name("preflight.py")
        env = dict(__import__("os").environ)
        env.pop("GOOGLE_API_KEY", None)
        env["GEMINI_API_KEY"] = "unit-test-secret-must-not-appear"
        result = subprocess.run(
            [sys.executable, str(preflight), "--upstream", str(upstream)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        check = next(item for item in report["checks"] if item["id"] == "gemini_api_key")
        self.assertTrue(check["passed"])
        self.assertIn("GEMINI_API_KEY", check["detail"])
        self.assertNotIn("unit-test-secret-must-not-appear", result.stdout)


if __name__ == "__main__":
    unittest.main()
