import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "experiment.py"
SPEC = importlib.util.spec_from_file_location("action_threshold_experiment", MODULE_PATH)
experiment = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = experiment
SPEC.loader.exec_module(experiment)


class ExperimentMechanicsTests(unittest.TestCase):
    def test_safe_path_rejects_escape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaises(ValueError):
                experiment.safe_path(root, "../escape")

    def test_trace_computes_pre_edit_boundary(self):
        trace = experiment.TraceState(started=experiment.time.monotonic())
        trace.record_tool("list_files", {"path": "."}, {"files": ["a.py"]})
        trace.record_tool("read_file", {"path": "a.py"}, {"path": "a.py", "content": "x"})
        trace.record_tool(
            "replace_text",
            {"path": "a.py", "old_text": "x", "new_text": "y"},
            {"ok": True, "path": "a.py"},
        )
        trace.record_tool("read_file", {"path": "b.py"}, {"path": "b.py", "content": "z"})
        metrics = experiment.pre_edit_metrics(trace.events, trace.first_edit_sequence)
        self.assertEqual(metrics["tool_calls_before_first_edit"], 2)
        self.assertEqual(metrics["unique_files_read_before_first_edit"], 1)
        self.assertEqual(metrics["files_read_before_first_edit"], ["a.py"])

    def test_first_patch_and_rework_are_recorded(self):
        trace = experiment.TraceState(started=experiment.time.monotonic())
        trace.record_tool("replace_text", {}, {"ok": True})
        trace.record_tool("run_tests", {}, {"passed": False})
        trace.record_tool("replace_text", {}, {"ok": True})
        self.assertFalse(trace.first_patch_test_passed)
        self.assertEqual(trace.edits_after_first_test, 1)

    def test_each_fixture_starts_failing_and_has_safe_test_command(self):
        for task_id in experiment.discover_tasks():
            task = experiment.load_task(task_id)
            self.assertEqual(task["test_command"][:4], ["python", "-m", "unittest", "discover"])
            with tempfile.TemporaryDirectory() as temp_dir:
                repo = Path(temp_dir) / "repo"
                experiment.shutil.copytree(task["source_repo"], repo)
                result = experiment.run_test_command(repo, task["test_command"])
                self.assertFalse(result["passed"], task_id)

    def test_summary_groups_models(self):
        base = {
            "task_id": "t",
            "final_test_passed": True,
            "first_patch_test_passed": True,
            "run_error": None,
            "tool_calls_before_first_edit": 1,
            "unique_files_read_before_first_edit": 1,
            "seconds_to_first_edit": 1.0,
            "edit_attempts_total": 1,
            "successful_edit_calls_total": 1,
            "edits_after_first_test": 0,
            "changed_file_count": 1,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
        summary = experiment.summarize([
            {**base, "model": "model-a"},
            {**base, "model": "model-b", "unique_files_read_before_first_edit": 3},
        ])
        self.assertEqual(summary["observation_count"], 2)
        self.assertEqual(len(summary["by_model"]), 2)

    def test_partial_summary_tolerates_missing_model_task_cell(self):
        rows = [
            {
                "model": "model-a",
                "task_id": "task-one",
                "final_test_passed": True,
                "first_patch_test_passed": None,
                "run_error": None,
                "tool_calls_before_first_edit": 1,
                "unique_files_read_before_first_edit": 1,
                "seconds_to_first_edit": 1.0,
                "edit_attempts_total": 1,
                "successful_edit_calls_total": 1,
                "edits_after_first_test": 0,
                "changed_file_count": 1,
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
            {
                "model": "model-b",
                "task_id": "task-two",
                "final_test_passed": True,
                "first_patch_test_passed": None,
                "run_error": None,
                "tool_calls_before_first_edit": 1,
                "unique_files_read_before_first_edit": 1,
                "seconds_to_first_edit": 1.0,
                "edit_attempts_total": 1,
                "successful_edit_calls_total": 1,
                "edits_after_first_test": 0,
                "changed_file_count": 1,
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        ]
        summary = experiment.summarize(rows)
        missing = summary["by_task"][0]["models"][1]
        self.assertEqual(missing["runs"], 0)
        self.assertIsNone(missing["final_pass_rate"])


if __name__ == "__main__":
    unittest.main()
