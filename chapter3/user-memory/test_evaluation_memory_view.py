"""Regression coverage for evaluation menu memory display."""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main
from config import MemoryMode


def test_evaluation_option_two_prints_memory_manager_context(monkeypatch, capsys):
    class FakeTestSuite:
        test_cases = [object()]

    class FakeFramework:
        def __init__(self):
            self.test_suite = FakeTestSuite()

    fake_framework_module = types.SimpleNamespace(UserMemoryEvaluationFramework=FakeFramework)
    monkeypatch.setitem(sys.modules, "models", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "evaluator", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "framework", fake_framework_module)

    class FakeMemoryManager:
        def get_context_string(self):
            return "User Memory Notes:\n\nNote 1: Prefers Python"

    class FakeConversationHistory:
        def __init__(self):
            self.conversations = []

    class FakeAgent:
        def __init__(self, *args, **kwargs):
            self.memory_manager = FakeMemoryManager()
            self.conversation_history = FakeConversationHistory()
            self.conversation = []

    class FakeProcessor:
        def __init__(self, *args, **kwargs):
            self.memory_manager = FakeMemoryManager()

    inputs = iter(["2", "4"])
    monkeypatch.setattr(main.Config, "get_api_key", lambda provider: "test-key")
    monkeypatch.setattr(main, "ConversationalAgent", FakeAgent)
    monkeypatch.setattr(main, "BackgroundMemoryProcessor", FakeProcessor)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    main.run_evaluation_mode("default_user", MemoryMode.NOTES, provider="moonshot", model="test-model")

    output = capsys.readouterr().out
    assert "Current Memory State" in output
    assert "Note 1: Prefers Python" in output
