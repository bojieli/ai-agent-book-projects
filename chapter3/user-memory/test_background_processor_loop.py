"""
Regression test for https://github.com/bojieli/ai-agent-book/issues/181

BackgroundMemoryProcessor entered an infinite processing loop because:
1. Its ConversationHistory instance loaded the history file once at startup
   and never reloaded, so turns saved by the main agent's separate instance
   were invisible -> process_recent_conversations() always returned early.
2. On that early return, last_processed_count was never updated, so
   should_process() stayed True and the background thread re-triggered
   every second forever.

This test simulates the interactive-mode flow without any API calls.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Use an isolated data dir and a dummy API key before importing project modules
_tmpdir = tempfile.mkdtemp(prefix="user_memory_test_")
os.environ["CONVERSATION_HISTORY_DIR"] = os.path.join(_tmpdir, "conversations")
os.environ.setdefault("MOONSHOT_API_KEY", "test-dummy-key")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
Config.create_directories()

from conversation_history import ConversationHistory
from background_memory_processor import BackgroundMemoryProcessor


class TestBackgroundProcessorLoop(unittest.TestCase):
    def setUp(self):
        self.user_id = "test_user_loop"
        history_file = os.path.join(
            os.environ["CONVERSATION_HISTORY_DIR"], f"{self.user_id}_history.json"
        )
        if os.path.exists(history_file):
            os.remove(history_file)

    def _make_processor(self):
        processor = BackgroundMemoryProcessor(
            user_id=self.user_id, provider="kimi", verbose=False
        )
        # Avoid real LLM calls: analysis is a no-op
        processor.analyze_conversation = lambda ctx: []
        return processor

    def test_new_turns_from_other_instance_are_seen(self):
        """Processor must see turns saved by a separate ConversationHistory."""
        processor = self._make_processor()

        # Simulate the main agent saving a turn through its own instance
        agent_history = ConversationHistory(self.user_id)
        agent_history.add_turn("session-1", "你好，我是小明", "你好小明！")

        processor.increment_conversation_count()
        self.assertTrue(processor.should_process())

        results = processor.process_recent_conversations()

        self.assertEqual(results.get("analyzed_turns"), 1)
        self.assertEqual(processor.last_processed_count, 1)
        self.assertFalse(processor.should_process())

    def test_no_infinite_loop_when_nothing_new(self):
        """should_process() must go False after a no-op processing run."""
        processor = self._make_processor()

        processor.increment_conversation_count()
        results = processor.process_recent_conversations()
        self.assertIn("message", results)  # early return: nothing to process
        self.assertFalse(
            processor.should_process(),
            "should_process() stayed True after no-op run -> infinite loop",
        )

        # And it must trigger again once a new conversation arrives
        processor.increment_conversation_count()
        self.assertTrue(processor.should_process())


if __name__ == "__main__":
    unittest.main()
