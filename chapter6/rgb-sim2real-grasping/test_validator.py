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

    def test_without_randomization_is_not_a_transfer_claim(self):
        data = {"schema_version": "3.0", "experiment_id": "9-10", "status": "complete", "kind": "local_gpu_rgb_domain_transfer", "metrics": {"device": {"device": "mps"}, "protocol": {"seeds": [1, 2, 3], "variants": ["source_clean", "source_background", "source_appearance", "source_full"], "target_domains": ["a", "b"], "total_training_examples": 24576}, "summary": {"source_clean": {"source": {"mean": 0.95}, "a": {"mean": 0.7}, "b": {"mean": 0.7}}, "source_full": {"a": {"mean": 0.8}, "b": {"mean": 0.8}}}, "dataset_replay_match": True}, "artifacts": [], "hardware_extension": {"actuation_attempted": False}}
        self.assertTrue(validate(data))


if __name__ == "__main__":
    unittest.main()
