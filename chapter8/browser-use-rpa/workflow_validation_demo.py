"""Offline state-machine demo for validated browser workflow learning.

It uses the same Workflow/StatePredicate schema as the Playwright replayer,
but replaces a real site with a deterministic page state. This makes the
candidate -> reset -> replay -> validated -> invalid lifecycle reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable

from learning_agent.workflow import (
    ActionType,
    PredicateType,
    StatePredicate,
    Workflow,
    WorkflowStep,
)


@dataclass
class SimulatedPage:
    url: str
    visible_elements: set[str] = field(default_factory=set)
    element_text: Dict[str, str] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)


def _check(page: SimulatedPage, predicate: StatePredicate) -> tuple[bool, Any]:
    if predicate.predicate_type == PredicateType.URL_CONTAINS:
        return str(predicate.expected) in page.url, page.url
    if predicate.predicate_type == PredicateType.ELEMENT_VISIBLE:
        actual = predicate.selector in page.visible_elements
        return actual == bool(predicate.expected), actual
    if predicate.predicate_type == PredicateType.ELEMENT_TEXT_CONTAINS:
        actual = page.element_text.get(predicate.selector or "", "")
        return str(predicate.expected) in actual, actual
    if predicate.predicate_type == PredicateType.PAGE_STATE_EQUALS:
        actual = page.state.get(predicate.state_key or "")
        return actual == predicate.expected, actual
    return False, "unsupported predicate"


def _assert_all(page: SimulatedPage, predicates: Iterable[StatePredicate], location: str) -> None:
    for predicate in predicates:
        passed, actual = _check(page, predicate)
        if not passed:
            label = predicate.description or predicate.predicate_type.value
            raise RuntimeError(
                f"{location}: {label}; expected={predicate.expected!r}, actual={actual!r}"
            )


def replay(workflow: Workflow, page: SimulatedPage) -> Dict[str, Any]:
    completed = 0
    try:
        for index, step in enumerate(workflow.steps, 1):
            _assert_all(page, step.preconditions, f"step {index} precondition")
            effect = step.parameters.get("simulated_effect", {})
            if "url" in effect:
                page.url = effect["url"]
            page.state.update(effect.get("state", {}))
            page.element_text.update(effect.get("element_text", {}))
            page.visible_elements.difference_update(effect.get("hide", []))
            page.visible_elements.update(effect.get("show", []))
            _assert_all(page, step.postconditions, f"step {index} postcondition")
            completed += 1
        _assert_all(page, workflow.final_predicates, "workflow final predicate")
        return {"success": True, "steps_completed": completed, "fallback_required": False, "error": None}
    except RuntimeError as error:
        return {
            "success": False,
            "steps_completed": completed,
            "fallback_required": True,
            "error": str(error),
        }


def candidate_workflow() -> Workflow:
    step = WorkflowStep(
        action_type=ActionType.CLICK,
        css_selector="#send",
        description="send message",
        parameters={
            "simulated_effect": {
                "url": "https://mail.example/sent/42",
                "state": {"sent": True},
                "element_text": {"#status": "Message sent"},
            }
        },
        preconditions=[StatePredicate(
            PredicateType.ELEMENT_VISIBLE, True, selector="#send",
            description="send button is visible",
        )],
        postconditions=[
            StatePredicate(
                PredicateType.PAGE_STATE_EQUALS, True, state_key="sent",
                description="message state changed to sent",
            ),
            StatePredicate(
                PredicateType.URL_CONTAINS, "/sent/",
                description="browser reached the sent-message page",
            ),
        ],
    )
    return Workflow(
        workflow_id="send-message-v1",
        intent="send a message",
        initial_url="https://mail.example/compose",
        steps=[step],
        final_predicates=[StatePredicate(
            PredicateType.ELEMENT_TEXT_CONTAINS,
            "Message sent",
            selector="#status",
            description="success confirmation is visible",
        )],
    )


def reset_environment() -> SimulatedPage:
    return SimulatedPage(
        url="https://mail.example/compose",
        visible_elements={"#send"},
        element_text={"#status": "Draft"},
        state={"sent": False},
    )


def changed_environment() -> SimulatedPage:
    return SimulatedPage(
        url="https://mail.example/compose-v2",
        visible_elements={"#send-v2"},
        element_text={"#status": "Draft"},
        state={"sent": False},
    )


def validate_candidate(workflow: Workflow) -> Dict[str, Any]:
    result = replay(workflow, reset_environment())
    if result["success"]:
        workflow.mark_validated()
    return result


def main() -> None:
    workflow = candidate_workflow()
    print(f"first-run artifact: {workflow.validation_status.value}")
    validation = validate_candidate(workflow)
    print(f"reset-and-replay: success={validation['success']}, status={workflow.validation_status.value}")

    changed = replay(workflow, changed_environment())
    if not changed["success"]:
        workflow.mark_invalid(changed["error"])
    print(f"after page change: success={changed['success']}, status={workflow.validation_status.value}")
    print(f"fallback to full Agent: {changed['fallback_required']}")
    print(f"reason: {changed['error']}")


if __name__ == "__main__":
    main()
