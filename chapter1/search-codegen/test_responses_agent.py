from agent import GPT5NativeAgent
from run_experiment_1_3 import validate_asean, validate_clarification


def test_request_uses_official_responses_tool_shapes():
    agent = GPT5NativeAgent("key")
    request = agent._build_responses_request(
        "task", reasoning_effort="max", verbosity="high"
    )
    assert request["reasoning"] == {"effort": "max"}
    assert request["text"] == {"verbosity": "high"}
    assert request["tools"] == [
        {"type": "web_search", "search_context_size": "medium"},
        {
            "type": "code_interpreter",
            "container": {"type": "auto", "memory_limit": "4g"},
        },
    ]


def test_asean_acceptance_requires_both_completed_hosted_tools():
    result = {
        "success": True,
        "requested_model": "gpt-5.6-sol",
        "model": "gpt-5.6-sol",
        "response": "Singapore and Kuala Lumpur are 316 km apart.",
        "output_items": [
            {"type": "web_search_call", "status": "completed"},
            {"type": "code_interpreter_call", "status": "completed"},
        ],
        "citations": [
            {"type": "url_citation", "url": "https://one.test"},
            {"type": "url_citation", "url": "https://two.test"},
        ],
    }
    assert validate_asean(result)["passed"] is True
    result["output_items"] = result["output_items"][:1]
    assert validate_asean(result)["passed"] is False


def test_clarification_requires_no_tools_then_linked_tool_run():
    first = {
        "success": True,
        "response": "Which source and indicators do you prefer?",
        "tool_calls": [],
        "response_id": "resp_1",
    }
    second = {
        "success": True,
        "request": {"previous_response_id": "resp_1"},
        "output_items": [
            {"type": "web_search_call", "status": "completed"},
            {"type": "code_interpreter_call", "status": "completed"},
        ],
        "citations": [{"type": "url_citation"}],
    }
    assert validate_clarification(first, second)["passed"] is True
