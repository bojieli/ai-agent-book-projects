import asyncio
import tempfile
import unittest

from learning_agent import KnowledgeBase
from learning_agent.workflow import WorkflowStatus
from local_mail_sandbox import mail_sandbox
from run_experiment_9_5 import FIRST, TRANSFER, compile_workflow, replay


CAPTURED = [
    {"action": "input_text", "selector": "#recipient", "value_key": "recipient"},
    {"action": "input_text", "selector": "#subject", "value_key": "subject"},
    {"action": "input_text", "selector": "#content", "value_key": "content"},
    {"action": "click", "selector": "#send", "value_key": None},
]


class RealPlaywrightCampaignTest(unittest.TestCase):
    def test_real_chromium_reset_replay_and_change_invalidation(self):
        async def scenario():
            with mail_sandbox() as (base_url, state), tempfile.TemporaryDirectory() as directory:
                workflow = compile_workflow(base_url, CAPTURED)
                store = KnowledgeBase(directory)
                store.save_candidate(workflow)
                self.assertEqual(WorkflowStatus.CANDIDATE, workflow.validation_status)

                state.reset(version=1)
                validation = await replay(workflow, FIRST)
                self.assertTrue(validation["success"])
                workflow.mark_validated()
                store.publish_validated(workflow)

                state.reset(version=1)
                transfer = await replay(workflow, TRANSFER)
                self.assertTrue(transfer["success"])
                self.assertEqual([TRANSFER], state.snapshot()["messages"])

                state.reset(version=2)
                before = len([e for e in state.snapshot()["events"] if e["event"] == "send_request"])
                changed = await replay(workflow, TRANSFER)
                after = len([e for e in state.snapshot()["events"] if e["event"] == "send_request"])
                self.assertFalse(changed["success"])
                self.assertTrue(changed["fallback_required"])
                self.assertEqual(before, after)
        asyncio.run(scenario())

    def test_naive_action_count_false_success_is_detected(self):
        async def scenario():
            with mail_sandbox() as (base_url, state):
                workflow = compile_workflow(base_url, CAPTURED)
                bad = {**TRANSFER, "content": ""}
                state.reset(version=1)
                naive = await replay(workflow, bad, validate_state=False)
                self.assertTrue(naive["success"])
                self.assertEqual([], state.snapshot()["messages"])
                state.reset(version=1)
                checked = await replay(workflow, bad, validate_state=True)
                self.assertFalse(checked["success"])
                self.assertEqual([], state.snapshot()["messages"])
        asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
