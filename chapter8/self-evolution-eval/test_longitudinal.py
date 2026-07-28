import json
import unittest
from pathlib import Path

from agent import ReferenceAgent
from harness import LongitudinalEvaluator


TASKS = json.loads(Path(__file__).with_name("dataset.json").read_text(encoding="utf-8"))["tasks"]


class LongitudinalEvaluationTest(unittest.TestCase):
    def test_evolving_agent_transfers_updates_and_retains(self):
        report = LongitudinalEvaluator().run(ReferenceAgent("evolving"), TASKS)
        self.assertEqual(1.0, report["transfer_accuracy"])
        self.assertEqual(1, report["adaptation"]["tasks_after_change_signal_to_recover"])
        self.assertEqual(1.0, report["retention_rate"])
        self.assertGreater(report["cost"]["storage_bytes"], 0)

    def test_append_only_agent_cannot_replace_changed_rule(self):
        report = LongitudinalEvaluator().run(ReferenceAgent("append_only"), TASKS)
        self.assertEqual(0.0, report["phase_accuracy"]["change"])
        self.assertLess(report["retention_rate"], 1.0)
        self.assertGreater(report["negative_transfer_rate"], 0.0)

    def test_static_agent_does_not_look_like_continual_learning(self):
        report = LongitudinalEvaluator().run(ReferenceAgent("static"), TASKS)
        self.assertEqual(0.0, report["transfer_accuracy"])
        self.assertEqual(0, report["cost"]["storage_bytes"])

    def test_all_four_phases_are_reported(self):
        report = LongitudinalEvaluator().run(ReferenceAgent("evolving"), TASKS)
        self.assertEqual({"learning", "transfer", "change", "retention"}, set(report["phase_accuracy"]))
        self.assertEqual(6, len(report["learning_curve"]))


if __name__ == "__main__":
    unittest.main()
