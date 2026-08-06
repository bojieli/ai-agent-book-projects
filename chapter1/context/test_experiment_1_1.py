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
    hidden = {"role": "tool", "content": "[Tool result hidden due to context mode]"}
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
