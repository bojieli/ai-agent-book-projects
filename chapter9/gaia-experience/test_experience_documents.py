import json
import tempfile
import unittest
from pathlib import Path

from experience_documents import build_documents, evaluate_retrieval_baselines, outcome_label, write_documents


class ExperienceDocumentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dataset = json.loads(Path(__file__).with_name("sample_trajectories.json").read_text(encoding="utf-8"))
        cls.records = dataset["learning_trajectories"]
        cls.cases = dataset["transfer_cases"]
        cls.documents = build_documents(cls.records, validated_on="2026-07-24")

    def test_outcome_has_partial_state(self):
        self.assertEqual("success", outcome_label(0.95))
        self.assertEqual("partial", outcome_label(0.45))
        self.assertEqual("failure", outcome_label(0.1))

    def test_markdown_is_cross_trajectory_document(self):
        web = next(item for item in self.documents if item.task_family == "web_research")
        markdown = web.to_markdown()
        self.assertIn("## 推荐策略", markdown)
        self.assertIn("## 常见误区", markdown)
        self.assertIn("gaia-web-01 (success", markdown)
        self.assertIn("gaia-web-03 (failure", markdown)
        self.assertIn("verify the answer with a primary source", markdown)
        self.assertNotIn("stop at the first search result", web.recommended_strategies)

    def test_document_baseline_transfers_without_negative_guidance(self):
        report = evaluate_retrieval_baselines(self.records, self.documents, self.cases)
        knowledge = report["knowledge_document"]
        self.assertEqual(1.0, knowledge["transfer_success_rate"])
        self.assertEqual(0.0, knowledge["negative_transfer_rate"])
        self.assertGreater(knowledge["average_retrieved_characters"], 0)

    def test_writes_markdown_files(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = write_documents(self.documents, Path(directory))
            self.assertEqual(2, len(paths))
            self.assertTrue(all(path.suffix == ".md" for path in paths))

    def test_build_documents_tolerates_missing_environment_score(self):
        # outcome_label already reads the score with .get(default); the sources
        # line must too, otherwise a record missing environment_score raises
        # KeyError instead of scoring 0.0.
        record = {
            "id": "gaia-x",
            "task_family": "web_research",
            "observed_strategies": ["s"],
            "mistakes": [],
            "exceptions": [],
            "applies_when": [],
            "capabilities": [],
        }
        documents = build_documents([record])
        self.assertEqual(1, len(documents))
        self.assertIn("gaia-x (failure, score=0.00)", documents[0].sources)


if __name__ == "__main__":
    unittest.main()
