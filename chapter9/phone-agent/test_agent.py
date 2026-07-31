from types import SimpleNamespace

import pytest
from agent import direct_plan, local_conversation_turn, react_plan


class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["response_format"] == {"type": "json_object"}
        content = """{
          "callee_name": "Jane",
          "goal": "Confirm a dental checkup time",
          "context": "Jane needs a dental checkup",
          "instructions": "Ask for the missing time, repeat it, then call complete_task.",
          "opening_line": "Hello Jane, I am calling to confirm your dental checkup time.",
          "missing_information": ["appointment time"],
          "decision_summary": "The time is missing, so collect it during the call."
        }"""
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


class FakeClient:
    chat = SimpleNamespace(completions=FakeCompletions())


def test_direct_plan_requires_the_fixed_parameters():
    with pytest.raises(ValueError, match="context"):
        direct_plan(callee_name="Jane", goal="Confirm", context="", instructions="Ask")


def test_react_plan_records_missing_information_and_trace():
    plan = react_plan("Call Jane, but I forgot the time", client=FakeClient(), model="planner-test")
    assert plan.mode == "react"
    assert plan.missing_information == ["appointment time"]
    assert [item["stage"] for item in plan.trace] == ["observation", "reason", "action"]
    assert plan.planner_model == "injected:planner-test"


def test_local_conversation_requires_explicit_confirmation():
    plan = direct_plan(
        callee_name="Jane",
        goal="Confirm a time",
        context="Tuesday afternoon",
        instructions="Ask and confirm",
    )
    incomplete = local_conversation_turn(plan, "Tuesday at 3pm could work")
    assert incomplete["should_complete"] is False
    completed = local_conversation_turn(plan, "I confirm Tuesday at 3pm with code RTC-92")
    assert completed["should_complete"] is True
    assert completed["completion"]["appointment_time"] == "Tuesday at 3pm"
    assert completed["completion"]["confirmation_number"] == "RTC-92"
