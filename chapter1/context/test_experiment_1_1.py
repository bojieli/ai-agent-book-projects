from agent import AgentTrajectory, ContextMode
from run_experiment_1_1 import (
    canonical_answer_correct,
    evaluate_context_contract,
    summarize_arm,
)


def turn(messages, *, tools=True, reasoning="reason"):
    request = {"messages": messages}
    if tools:
        request.update({"tools": [{"type": "function"}], "tool_choice": "auto"})
    return {
        "request": request,
        "response": {
            "id": "real-response-id",
            "choices": [{"message": {"reasoning_content": reasoning}}],
        },
    }


SYSTEM = {"role": "system", "content": "system"}
USER = {"role": "user", "content": "task"}
ASSISTANT = {
    "role": "assistant",
    "reasoning_content": "reason",
    "tool_calls": [{"id": "call"}],
}
TOOL = {"role": "tool", "content": '{"result": 4}'}


def test_full_contract_uses_raw_followup_context():
    result = evaluate_context_contract(
        "full", [turn([SYSTEM, USER]), turn([SYSTEM, USER, ASSISTANT, TOOL])]
    )
    assert result["passed"] is True


def test_no_history_contract_rejects_sliding_window():
    exact = evaluate_context_contract(
        "no_history", [turn([SYSTEM, USER]), turn([SYSTEM, USER])]
    )
    sliding = evaluate_context_contract(
        "no_history", [turn([SYSTEM, USER]), turn([SYSTEM, USER, ASSISTANT, TOOL])]
    )
    assert exact["passed"] is True
    assert sliding["passed"] is False


def test_no_reasoning_requires_provider_reasoning_but_stripped_history():
    stripped_assistant = {k: v for k, v in ASSISTANT.items() if k != "reasoning_content"}
    result = evaluate_context_contract(
        "no_reasoning",
        [turn([SYSTEM, USER]), turn([SYSTEM, USER, stripped_assistant, TOOL])],
    )
    assert result["passed"] is True


def test_no_tool_results_requires_literal_hidden_observations():
    hidden = {"role": "tool", "content": ""}
    result = evaluate_context_contract(
        "no_tool_results",
        [turn([SYSTEM, USER]), turn([SYSTEM, USER, ASSISTANT, hidden])],
    )
    assert result["passed"] is True
    leaked = evaluate_context_contract(
        "no_tool_results", [turn([SYSTEM, USER]), turn([SYSTEM, USER, ASSISTANT, TOOL])]
    )
    assert leaked["passed"] is False


def test_no_tool_definitions_requires_absent_request_fields():
    result = evaluate_context_contract("no_tool_calls", [turn([SYSTEM, USER], tools=False)])
    assert result["passed"] is True


def _arm_result(final_answer, *, mode=ContextMode.NO_TOOL_CALLS, iterations=1):
    completed = final_answer is not None
    return {
        "trajectory": AgentTrajectory(context_mode=mode),
        "final_answer": final_answer,
        "completed": completed,
        "success": completed,
        "iterations": iterations,
        "provider": "test",
        "model": "test-model",
    }


def test_canonical_answer_rubric_rejects_refusal_and_hallucinated_markup():
    refusal = "I cannot compute the exchange rates without tools."
    hallucinated = "<request_tool>currency_converter(...)</request_tool>"
    assert canonical_answer_correct(refusal) is False
    assert canonical_answer_correct(hallucinated) is False


def test_summarize_arm_separates_completion_from_task_success():
    result = summarize_arm(
        ContextMode.NO_TOOL_CALLS,
        _arm_result("I cannot compute the exchange rates without tools."),
        elapsed=0.1,
    )

    # The model did return a terminal response, but it did not complete the
    # canonical financial task. A mode-independent evaluator must preserve
    # that distinction instead of forcing the mode to fail.
    assert result["completed"] is True
    assert result["success"] is True  # compatibility alias
    assert result["task_success"] is False
    assert result["behavior"]["canonical_answer_correct"] is False


def test_summarize_arm_accepts_correct_answer_even_in_an_ablated_arm():
    answer = "Annual total: $9,602,895.73; quarterly average: $2,400,723.93"
    result = summarize_arm(
        ContextMode.NO_TOOL_RESULTS,
        _arm_result(answer, mode=ContextMode.NO_TOOL_RESULTS),
        elapsed=0.1,
    )

    # Correctness is an observed task result. The experiment may separately
    # report that tool feedback was hidden; it must not manufacture failure.
    assert result["completed"] is True
    assert result["task_success"] is True
    assert result["behavior"]["canonical_answer_correct"] is True


def _live_arm(mode, *, behavior, outcome="correct", groundedness_verdict="not_assessable", error=None):
    """Build a minimal summarised arm for the analysis-level tests."""
    return {
        "mode": mode,
        "using_openrouter": False,
        "error": error,
        "api_turns": [{"response": {"id": "real-response-id"}}],
        "context_contract": {"passed": True},
        "groundedness": {"verdict": groundedness_verdict},
        "outcome": outcome,
        "behavior": behavior,
    }


def test_arm_outcome_separates_claiming_nothing_from_inventing():
    from run_experiment_1_1 import arm_outcome

    assert arm_outcome(False, False, "no_answer") == "no_terminal_response"
    # A turn that only narrated its plan claims no figure either, and the
    # harness does not pretend to tell that from a principled refusal.
    assert arm_outcome(True, False, "no_quantities") == "no_unsupported_numbers"
    assert arm_outcome(True, True, "not_assessable") == "correct"
    # Both of these are "Completed" in the legacy table; only one is safe.
    assert arm_outcome(True, False, "grounded") == "no_unsupported_numbers"
    assert arm_outcome(True, False, "ungrounded") == "unsupported_numbers"
    assert arm_outcome(True, False, "not_assessable") == "incorrect"


def test_summarize_arm_flags_numbers_no_observation_supports():
    from run_experiment_1_1 import summarize_arm

    invented = (
        "Q2 -> $2,268,000; Q3 -> $2,286,000; Q4 -> $2,451,612.90. "
        "Annual total $9,505,612.90."
    )
    arm = summarize_arm(ContextMode.NO_TOOL_CALLS, _arm_result(invented), elapsed=0.1)

    assert arm["completed"] is True  # the legacy column still says ✓
    assert arm["task_success"] is False
    assert arm["outcome"] == "unsupported_numbers"
    assert arm["behavior"]["stated_unsupported_numbers"] is True


def test_a_run_that_never_reached_the_provider_observes_no_claims():
    from run_experiment_1_1 import analyze

    # Every arm errored before inference. Two of the manuscript's claims are
    # phrased as absences, so a naive reading would score them "observed".
    dead = [
        {
            "mode": mode.value,
            "using_openrouter": False,
            "error": "Error code: 402",
            "api_turns": [{"error": "Error code: 402"}],
            "context_contract": {"passed": False},
            "groundedness": {"verdict": "no_answer"},
            "outcome": "no_terminal_response",
            "behavior": {
                "tool_action_count": 0,
                "has_repeated_tool_action": False,
                "canonical_answer_correct": False,
            },
        }
        for mode in ContextMode
    ]
    claims = analyze(dead)["manuscript_behavior_claims"]

    assert claims["without_tool_definitions_no_tool_action"] is None
    assert claims["without_reasoning_degraded"] is None
    assert claims["all_manuscript_behavior_claims_observed"] is False


def test_analysis_reports_which_arms_stated_unsupported_numbers():
    from run_experiment_1_1 import analyze

    arms = [
        _live_arm(
            "no_tool_calls",
            behavior={
                "tool_action_count": 0,
                "has_repeated_tool_action": False,
                "canonical_answer_correct": False,
            },
            outcome="unsupported_numbers",
            groundedness_verdict="ungrounded",
        )
    ]
    analysis = analyze(arms)

    assert analysis["arm_outcomes"] == {"no_tool_calls": "unsupported_numbers"}
    assert analysis["arms_stating_unsupported_numbers"] == ["no_tool_calls"]
    # The "no tool action" claim holds, but the qualification says why that is
    # not an observation about the model.
    assert analysis["manuscript_behavior_claims"][
        "without_tool_definitions_no_tool_action"
    ] is True
    assert "Vacuous by construction" in analysis["claim_qualifications"][
        "without_tool_definitions_no_tool_action"
    ]


def test_hidden_result_contract_follows_the_configured_style():
    from agent import HIDDEN_RESULT_STYLES
    from run_experiment_1_1 import evaluate_context_contract

    empty = {"role": "tool", "content": ""}
    marker = {"role": "tool", "content": HIDDEN_RESULT_STYLES["marker"]}

    # Withholding silently is a different experiment from leaving a visible
    # redaction, so each run is checked against the style it configured, and
    # neither is accepted in place of the other.
    silent = evaluate_context_contract(
        "no_tool_results",
        [turn([SYSTEM, USER]), turn([SYSTEM, USER, ASSISTANT, empty])],
        HIDDEN_RESULT_STYLES["empty"],
    )
    assert silent["passed"] is True

    mismatched = evaluate_context_contract(
        "no_tool_results",
        [turn([SYSTEM, USER]), turn([SYSTEM, USER, ASSISTANT, marker])],
        HIDDEN_RESULT_STYLES["empty"],
    )
    assert mismatched["passed"] is False

    # A real observation still fails either way.
    leaked = evaluate_context_contract(
        "no_tool_results",
        [turn([SYSTEM, USER]), turn([SYSTEM, USER, ASSISTANT, TOOL])],
        HIDDEN_RESULT_STYLES["empty"],
    )
    assert leaked["passed"] is False
