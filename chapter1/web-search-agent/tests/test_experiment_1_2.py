from run_experiment_1_2 import fiber_ids, validate


def formula_tool():
    return {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
    }


def test_fiber_ids_only_accept_real_succeeded_receipts():
    turns = [
        {
            "kind": "formula_fiber",
            "http_status": 200,
            "response": {"id": "fiber-one", "status": "succeeded"},
        },
        {
            "kind": "formula_fiber",
            "http_status": 200,
            "response": {"id": "fiber-failed", "status": "failed"},
        },
        {
            "kind": "chat_completion",
            "http_status": 200,
            "response": {"id": "chat-one"},
        },
    ]
    assert fiber_ids(turns) == ["fiber-one"]


def test_acceptance_requires_distinct_sequential_formula_fibers_and_links():
    tool = formula_tool()
    turns = [
        {
            "kind": "formula_tools",
            "formula_uri": "moonshot/web-search:latest",
            "request": {
                "method": "GET",
                "url": "https://api.moonshot.cn/v1/formulas/moonshot/web-search:latest/tools",
            },
            "http_status": 200,
            "response": {"tools": [tool]},
        },
        {
            "kind": "chat_completion",
            "request": {"tools": [tool]},
            "response": {"id": "chat-1", "usage": {}},
        },
        {
            "kind": "formula_fiber",
            "formula_uri": "moonshot/web-search:latest",
            "request": {
                "body": {
                    "name": "web_search",
                    "arguments": '{"query":"ASEAN capitals"}',
                }
            },
            "http_status": 200,
            "response": {"id": "fiber-one", "status": "succeeded"},
        },
        {
            "kind": "chat_completion",
            "request": {"tools": [tool]},
            "response": {"id": "chat-2", "usage": {}},
        },
        {
            "kind": "formula_fiber",
            "formula_uri": "moonshot/web-search:latest",
            "request": {
                "body": {
                    "name": "web_search",
                    "arguments": '{"query":"ASEAN capital coordinates"}',
                }
            },
            "http_status": 200,
            "response": {"id": "fiber-two", "status": "succeeded"},
        },
        {
            "kind": "chat_completion",
            "request": {"tools": [tool]},
            "response": {"id": "chat-3", "usage": {}},
        },
    ]
    payload = {
        "provider": "moonshot",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "kimi-k3",
        "answer": (
            "检索日期 2026-07-30：东盟现有 11（十一）个成员，"
            "Timor-Leste（东帝汶）于 2025-10-26 加入。"
            "雅加达 Jakarta 在总统令生效前仍是首都，Nusantara 为迁都目标。"
            "https://asean.org/example https://inp.polri.go.id/example"
        ),
        "trace": [
            {
                "iteration": 1,
                "type": "action",
                "tool": "web_search",
                "args": {"query": "ASEAN capitals"},
            },
            {"iteration": 1, "type": "thought"},
            {
                "iteration": 2,
                "type": "action",
                "tool": "web_search",
                "args": {"query": "ASEAN capital coordinates"},
            },
            {"iteration": 3, "type": "answer"},
        ],
        "api_turns": turns,
    }
    assert validate(payload)["passed"] is True


def test_acceptance_rejects_two_fibers_from_one_search_round():
    tool = formula_tool()
    payload = {
        "provider": "moonshot",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "kimi-k3",
        "answer": (
            "2026-07-30：11 个成员，东帝汶 Timor-Leste 于 2025-10-26 加入。"
            "雅加达 Jakarta 在总统令前仍是首都，Nusantara 努山塔拉待迁都。"
            "https://asean.org/a https://inp.polri.go.id/b"
        ),
        "trace": [
            {"iteration": 1, "type": "thought"},
            {
                "iteration": 1,
                "type": "action",
                "tool": "web_search",
                "args": {"query": "one"},
            },
            {
                "iteration": 1,
                "type": "action",
                "tool": "web_search",
                "args": {"query": "two"},
            },
            {"iteration": 2, "type": "answer"},
        ],
        "api_turns": [
            {
                "kind": "formula_tools",
                "formula_uri": "moonshot/web-search:latest",
                "http_status": 200,
                "response": {"tools": [tool]},
            },
            *[
                {
                    "kind": "chat_completion",
                    "request": {"tools": [tool]},
                    "response": {"id": f"chat-{i}", "usage": {}},
                }
                for i in range(3)
            ],
            *[
                {
                    "kind": "formula_fiber",
                    "formula_uri": "moonshot/web-search:latest",
                    "request": {
                        "body": {
                            "name": "web_search",
                            "arguments": f'{{"query":"{i}"}}',
                        }
                    },
                    "http_status": 200,
                    "response": {"id": f"fiber-{i}", "status": "succeeded"},
                }
                for i in range(2)
            ],
        ],
    }
    result = validate(payload)
    assert result["checks"]["sequential_search_rounds_observed"] is False
    assert result["passed"] is False
