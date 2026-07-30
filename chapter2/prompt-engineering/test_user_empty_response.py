from types import SimpleNamespace

from tau_bench.envs import user as user_module
from tau_bench.envs.user import LLMUserSimulationEnv
from ablation_agent import completion_token_limit


class Message:
    def __init__(self, content):
        self.content = content

    def model_dump(self):
        return {"role": "assistant", "content": self.content}


def response(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=Message(content))])


def test_empty_user_simulator_reply_is_retried_without_inserting_empty_message():
    env = LLMUserSimulationEnv(model="kimi-k3", provider="openai", seed=10)
    env.messages = [{"role": "system", "content": "simulate"}]
    replies = iter([response(""), response("A non-empty reply")])
    requests = []

    def fake_completion(messages):
        requests.append(messages)
        return next(replies)

    env._completion = fake_completion
    assert env.generate_next_message(env.messages) == "A non-empty reply"
    assert all(message.get("content") != "" for message in env.messages)
    assert "previous simulated-user reply was empty" in env.messages[-2]["content"]
    assert len(requests) == 2


def test_kimi_user_simulator_reserves_room_after_hidden_reasoning(monkeypatch):
    captured = []

    def fake_completion(**kwargs):
        captured.append(kwargs)
        return response("A visible user reply")

    monkeypatch.setattr(user_module, "completion", fake_completion)
    kimi = LLMUserSimulationEnv(model="kimi-k3", provider="openai", seed=10)
    kimi._completion([{"role": "system", "content": "simulate"}])
    assert captured[-1]["max_tokens"] == 4096

    ordinary = LLMUserSimulationEnv(model="gpt-4o-mini", provider="openai", seed=10)
    ordinary._completion([{"role": "system", "content": "simulate"}])
    assert captured[-1]["max_tokens"] == 1024


def test_kimi_action_model_reserves_room_after_hidden_reasoning():
    assert completion_token_limit("kimi-k3") == 8192
    assert completion_token_limit("gpt-4o-mini") == 4096
