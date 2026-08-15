import json
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

    def test_event_log_covers_every_formal_episode(self):
        evidence_dir = Path(__file__).parent / "validation" / "runs" / "local-gpu"
        evidence = evidence_dir / "evidence.json"
        event_log = evidence_dir / "predictive_episode_events.json"
        if not evidence.is_file() or not event_log.is_file():
            self.skipTest("run the local GPU experiment first")
        data = json.loads(evidence.read_text(encoding="utf-8"))
        payload = json.loads(event_log.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["episodes"]), data["metrics"]["protocol"]["total_episodes"])

    def test_unbounded_tools_are_rejected(self):
        data = {"schema_version": "3.0", "experiment_id": "9-9", "status": "complete", "kind": "desktop_manipulation_planning", "metrics": {"device": {"device": "mps"}, "protocol": {"seeds": [1, 2, 3], "failure_probabilities": [0.0, 0.25, 0.5], "total_episodes": 3456}, "models": [{"test_mse": 0.01}] * 3, "cells": [], "deterministic_replay": True}, "tool_contract": ["move_anywhere"], "artifacts": [], "xlerobot_robocrew_extension": {"actuation_attempted": False}}
        self.assertTrue(validate(data))


if __name__ == "__main__":
    unittest.main()
