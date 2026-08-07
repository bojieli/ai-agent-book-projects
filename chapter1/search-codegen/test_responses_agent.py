from agent import GPT5NativeAgent
from config import Config
from run_experiment_1_3 import (
    acceptance,
    independent_asean_reference,
    validate_asean,
    validate_clarification,
)

DASHSCOPE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"


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


def test_dashscope_request_uses_hosted_tool_shapes_and_streaming():
    agent = GPT5NativeAgent("key", base_url=DASHSCOPE_URL, model="qwen3.7-plus")
    assert agent.provider == "dashscope"
    request = agent._build_responses_request(
        "task", reasoning_effort="high", verbosity="high"
    )
    # DashScope runs thinking natively: no reasoning.effort or text.verbosity,
    # and streaming is mandatory because its gateway drops idle connections.
    assert "reasoning" not in request
    assert "text" not in request
    assert request["stream"] is True
    assert request["tools"] == [
        {"type": "web_search"},
        {"type": "code_interpreter"},
    ]


def test_config_resolves_dashscope_backend():
    key, base_url, model = Config.resolve("dashscope")
    assert base_url == DASHSCOPE_URL
    assert model == Config.DASHSCOPE_MODEL
    assert isinstance(key, str)


def test_dashscope_citations_from_web_search_sources():
    agent = GPT5NativeAgent("key", base_url=DASHSCOPE_URL, model="qwen3.7-plus")
    response = {
        "output": [
            {
                "type": "web_search_call",
                "status": "completed",
                "action": {
                    "query": "ASEAN capitals",
                    "sources": [
                        {"type": "url", "url": "https://asean.test/one"},
                        {"type": "url", "url": "https://asean.test/two"},
                    ],
                },
            }
        ]
    }
    citations = agent._citations(response)
    assert citations == [
        {"type": "url_citation", "url": "https://asean.test/one"},
        {"type": "url_citation", "url": "https://asean.test/two"},
    ]

def test_dashscope_citations_from_web_search_string_url_sources():
    agent = GPT5NativeAgent("key", base_url=DASHSCOPE_URL, model="qwen3.7-plus")
    response = {
        "output": [
            {
                "type": "web_search_call",
                "status": "completed",
                "action": {
                    "query": "ASEAN capitals",
                    "sources": [
                        "https://asean.test/one",
                        "https://asean.test/two",
                    ],
                },
            }
        ]
    }
    citations = agent._citations(response)
    assert citations == [
        {"type": "url_citation", "url": "https://asean.test/one"},
        {"type": "url_citation", "url": "https://asean.test/two"},
    ]


def test_independent_asean_reference_is_kuala_lumpur_singapore():
    reference = independent_asean_reference()
    assert reference["pair"] == ["Kuala Lumpur", "Singapore"]
    assert reference["pair_count"] == 45
    assert 250 < reference["distance_km"] < 400


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


def test_asean_acceptance_rejects_model_substitution():
    result = {
        "success": True,
        "requested_model": "qwen3.7-plus",
        "model": "qwen3.7-flash",
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
    assert validate_asean(result)["checks"]["model_identity_exact"] is False
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
        "response": "MA7, MA20, RSI14 and MACD(12,26,9) were computed.",
        "output_items": [
            {"type": "web_search_call", "status": "completed"},
            {"type": "code_interpreter_call", "status": "completed"},
        ],
        "citations": [{"type": "url_citation"}],
    }
    assert validate_clarification(first, second)["passed"] is True
    second_without_indicators = dict(second, response="Here is the report.")
    assert validate_clarification(first, second_without_indicators)["passed"] is False


def test_acceptance_is_multi_provider_not_openai_gated():
    passing_run = {
        "backend": "dashscope",
        "started": True,
        "requested_model": "qwen3.7-plus",
        "asean_validation": {"passed": True},
        "clarification": {"validation": {"passed": True}},
    }
    blocked_openai = {"backend": "openai", "started": True,
                      "requested_model": "gpt-5.6-sol",
                      "asean_validation": {"passed": False},
                      "clarification": {"validation": {"passed": False}}}
    result = acceptance([blocked_openai, passing_run])
    assert result["passed"] is True
    assert result["acceptance_backend"] == "dashscope"
    # OpenAI keeps priority when both pass.
    blocked_openai["asean_validation"] = {"passed": True}
    blocked_openai["clarification"] = {"validation": {"passed": True}}
    result = acceptance([blocked_openai, passing_run])
    assert result["acceptance_backend"] == "openai"
    # OpenRouter alone can never close the experiment.
    openrouter_run = dict(passing_run, backend="openrouter")
    result = acceptance([openrouter_run])
    assert result["passed"] is False
    assert result["openrouter_is_diagnostic_not_acceptance"] is True
