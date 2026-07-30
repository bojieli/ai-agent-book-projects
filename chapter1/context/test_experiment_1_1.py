from run_experiment_1_1 import evaluate_context_contract


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
