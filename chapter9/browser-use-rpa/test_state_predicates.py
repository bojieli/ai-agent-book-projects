import tempfile
import unittest

from learning_agent import KnowledgeBase
from learning_agent.workflow import WorkflowStatus
from workflow_validation_demo import (
    candidate_workflow,
    changed_environment,
    replay,
    validate_candidate,
)


class StatePredicateTest(unittest.TestCase):
    def test_candidate_must_pass_reset_replay_before_storage(self):
        workflow = candidate_workflow()
        self.assertEqual(WorkflowStatus.CANDIDATE, workflow.validation_status)
        with tempfile.TemporaryDirectory() as directory:
            store = KnowledgeBase(directory)
            store.save_candidate(workflow)
            with self.assertRaises(ValueError):
                store.save_workflow(workflow)

            result = validate_candidate(workflow)
            self.assertTrue(result["success"])
            store.publish_validated(workflow)
            self.assertIn(workflow.workflow_id, store.workflows)

    def test_page_change_invalidates_workflow_and_requests_fallback(self):
        workflow = candidate_workflow()
        validate_candidate(workflow)
        result = replay(workflow, changed_environment())
        self.assertFalse(result["success"])
        self.assertTrue(result["fallback_required"])
        self.assertIn("send button is visible", result["error"])

    def test_predicates_survive_serialization(self):
        original = candidate_workflow()
        restored = type(original).from_json(original.to_json())
        self.assertEqual("element_visible", restored.steps[0].preconditions[0].predicate_type.value)
        self.assertEqual("element_text_contains", restored.final_predicates[0].predicate_type.value)


if __name__ == "__main__":
    unittest.main()
