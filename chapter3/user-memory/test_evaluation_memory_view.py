"""Regression coverage for evaluation menu memory display."""
import builtins
import types
from pathlib import Path


def test_evaluation_option_two_prints_memory_manager_context(monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(Path(__file__).parent))

    import main
    from config import MemoryMode

    class FakeTestSuite:
        test_cases = [object()]

    class FakeFramework:
        def __init__(self):
            self.test_suite = FakeTestSuite()

    fake_evaluation_modules = {
        "config": types.SimpleNamespace(),
        "models": types.SimpleNamespace(),
        "evaluator": types.SimpleNamespace(),
        "framework": types.SimpleNamespace(UserMemoryEvaluationFramework=FakeFramework),
    }
    real_import = builtins.__import__

    def import_fake_evaluation_module(name, globals=None, locals=None, fromlist=(), level=0):
        if level == 0 and name in fake_evaluation_modules:
            return fake_evaluation_modules[name]
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_fake_evaluation_module)

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
