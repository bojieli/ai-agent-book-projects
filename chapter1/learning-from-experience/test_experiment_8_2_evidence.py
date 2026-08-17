import json
from types import SimpleNamespace

from experiment import ExperimentRunner
from game_environment import TreasureHuntGame
from llm_agent import LLMAgent
from run_experiment_8_2 import _write_json


class _Usage:
    total_tokens = 17

    def model_dump(self):
        return {"prompt_tokens": 10, "completion_tokens": 7, "total_tokens": 17}


def _response(content="Reasoning\n  **ACTION**: take rusty sword  "):
    message = SimpleNamespace(content=content, reasoning_content="private reasoning")
    choice = SimpleNamespace(message=message, finish_reason="stop")
    return SimpleNamespace(
        id="chatcmpl-real-shape",
        created=123,
        model="kimi-k3",
        choices=[choice],
        usage=_Usage(),
    )


def test_explicit_action_variants_are_recorded_without_fallback(monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-only")
    agent = LLMAgent(model="kimi-k3")
    agent.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_: _response())
        )
    )

    action = agent.choose_action(TreasureHuntGame(), verbose=False)

    assert action == "take rusty sword"
    assert agent.api_records[0]["fallback_used"] is False
    assert agent.api_records[0]["response"]["id"] == "chatcmpl-real-shape"
    assert agent.api_records[0]["response"]["reasoning_content"] == "private reasoning"
    assert agent.total_tokens == 17


def test_api_failure_is_retained_and_cannot_look_like_model_behavior(monkeypatch):
    monkeypatch.setenv("MOONSHOT_API_KEY", "test-only")
    agent = LLMAgent(model="kimi-k3")

    def fail(**_):
        raise RuntimeError("provider unavailable")

    agent.client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=fail))
    )
    action = agent.choose_action(TreasureHuntGame(), verbose=False)

    assert action in TreasureHuntGame().get_available_actions()
    assert agent.api_calls == 0
    assert agent.api_records[0]["fallback_used"] is True
    assert agent.api_records[0]["fallback_reason"] == "api_error"
    assert agent.api_records[0]["error"]["type"] == "RuntimeError"


def test_saved_evidence_excludes_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("MOONSHOT_API_KEY", "secret-that-must-not-be-written")
    agent = LLMAgent(model="kimi-k3")
    agent.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_: _response())
        )
    )
    agent.choose_action(TreasureHuntGame(), verbose=False)
    output = tmp_path / "llm_experiences.json"
    agent.save_experiences(output)
    payload = output.read_text(encoding="utf-8")

    assert "secret-that-must-not-be-written" not in payload
    assert json.loads(payload)["backend"]["provider"] == "moonshot"


def test_nested_validation_output_is_created(tmp_path):
    root = tmp_path / "validation" / "experiment_8_2"
    runner = ExperimentRunner(results_dir=str(root))
    assert runner.experiment_dir.parent == root
    assert runner.experiment_dir.is_dir()


def test_evidence_writer_serializes_numpy_scalars(tmp_path):
    import numpy as np

    output = tmp_path / "evidence.json"
    _write_json(output, {"gate": np.bool_(True), "count": np.int64(17)})
    assert json.loads(output.read_text(encoding="utf-8")) == {
        "gate": True,
        "count": 17,
    }
