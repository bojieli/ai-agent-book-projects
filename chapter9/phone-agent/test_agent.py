import json
from types import SimpleNamespace

import pytest
from agent import conversation_turn, direct_plan, react_plan


class FakeUsage:
    def model_dump(self, **_kwargs):
        return {"prompt_tokens": 40, "completion_tokens": 20, "total_tokens": 60}


class FakeResponse:
    def __init__(self, content):
        self.id = "provider-response-123"
        self.model = "planner-test"
        self.created = 123456
        self.usage = FakeUsage()
        self.choices = [
            SimpleNamespace(
                message=SimpleNamespace(content=content),
                finish_reason="stop",
            )
        ]

    def model_dump(self, **_kwargs):
        return {
            "id": self.id,
            "model": self.model,
            "created": self.created,
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": self.choices[0].message.content},
                }
            ],
            "usage": self.usage.model_dump(),
        }


class FakeCompletions:
    def __init__(self, values):
        self.values = iter(values)

    def create(self, **kwargs):
        assert kwargs["response_format"] == {"type": "json_object"}
        assert kwargs["temperature"] == 0
        return FakeResponse(json.dumps(next(self.values)))


class FakeClient:
    def __init__(self, values):
        self.chat = SimpleNamespace(completions=FakeCompletions(values))


@pytest.fixture(autouse=True)
def provider_environment(monkeypatch):
    monkeypatch.setenv("PHONE_MODEL_PROVIDER", "ark")
    monkeypatch.setenv("ARK_API_KEY", "test-key-not-retained")


def test_direct_plan_requires_fixed_parameters_and_has_no_planner_receipt():
    with pytest.raises(ValueError, match="context"):
        direct_plan(callee_name="Jane", goal="Confirm", context="", instructions="Ask")
    plan = direct_plan(callee_name="Jane", goal="Confirm", context="Tuesday", instructions="Ask")
    assert plan.planner_receipt is None
    assert "confirmation code" in plan.opening_line


def test_react_plan_retains_real_raw_receipt_and_trace():
    client = FakeClient(
        [
            {
                "callee_name": "Jane",
                "goal": "Confirm a dental checkup time",
                "context": "The time and code are absent.",
                "instructions": "Ask for time and code, repeat both, then complete_task.",
                "opening_line": "What exact time and confirmation code do you confirm?",
                "missing_information": ["appointment time", "confirmation code"],
                "decision_summary": "Collect both omitted fields by voice.",
            }
        ]
    )
    plan = react_plan(
        "Call Jane, but I forgot the time and code",
        client=client,
        model="planner-test",
        provider_name="injected-test",
    )
    assert plan.missing_information == ["appointment time", "confirmation code"]
    assert [item["stage"] for item in plan.trace] == ["observation", "reason", "action"]
    receipt = plan.planner_receipt
    assert receipt["provider_response_id"] == "provider-response-123"
    assert receipt["usage"]["total_tokens"] == 60
    assert receipt["raw_response"]["choices"][0]["message"]["content"]
    assert receipt["fallback_used"] is False
    assert "test-key-not-retained" not in json.dumps(receipt)


def test_conversation_requires_explicit_confirmation_for_completion():
    plan = direct_plan(
        callee_name="Jane",
        goal="Confirm a time",
        context="Tuesday afternoon",
        instructions="Ask and confirm",
    )
    client = FakeClient(
        [
            {
                "assistant_message": "Thanks. I recorded Tuesday at 3 PM and Maple 7.",
                "explicit_confirmation_observed": True,
                "should_complete": True,
                "completion": {
                    "result": "Local confirmation recorded.",
                    "appointment_time": "Tuesday at 3 PM",
                    "confirmation_number": "MAPLE-7",
                    "notes": "No external organization was contacted or booking made.",
                },
            }
        ]
    )
    result = conversation_turn(
        plan,
        [],
        "I explicitly confirm Tuesday at 3 PM and Maple seven.",
        client=client,
        model="planner-test",
        provider_name="injected-test",
    )
    assert result["should_complete"] is True
    assert result["completion"]["confirmation_number"] == "MAPLE-7"
    assert result["llm_receipt"]["purpose"] == "post_asr_dialogue"


def test_model_errors_propagate_without_fallback():
    class BrokenCompletions:
        def create(self, **_kwargs):
            raise RuntimeError("provider unavailable")

    client = SimpleNamespace(chat=SimpleNamespace(completions=BrokenCompletions()))
    with pytest.raises(RuntimeError, match="provider unavailable"):
        react_plan("Call Jane and ask for the missing time", client=client, model="planner-test")
def test_conversation_turn_rejects_none_critical_completion_fields():
    plan = direct_plan(
        callee_name="Jane",
        goal="Confirm a time",
        context="Tuesday afternoon",
        instructions="Ask and confirm",
    )
    client = FakeClient(
        [
            {
                "assistant_message": "Thanks.",
                "explicit_confirmation_observed": True,
                "should_complete": True,
                "completion": {
                    "result": "Local confirmation recorded.",
                    "appointment_time": None,
                    "confirmation_number": "MAPLE-7",
                    "notes": "No external organization was contacted or booking made.",
                },
            }
        ]
    )
    with pytest.raises(ValueError, match="without both critical fields"):
        conversation_turn(
            plan,
            [],
            "I explicitly confirm Maple seven.",
            client=client,
            model="planner-test",
            provider_name="injected-test",
        )
