"""回归测试：模型传错/漏工具参数时，编排器不应崩溃，而应把错误作为工具结果
回给模型（让它自行纠正），流程继续推进到最终回复。

此前 orchestrator.py 的 `impl(**args)` 未加保护：{"q": ...} 这类错键名、
缺必填参数、或无法 float() 转换的取值都会以 TypeError/ValueError 炸掉整个
多角色移交流程。
"""

import json
from types import SimpleNamespace

from orchestrator import MultiRoleOrchestrator

FINAL_TEXT = "已查完，最终汇报。"


def _tool_call_msg(name, arguments):
    tc = SimpleNamespace(
        id="call_1", type="function",
        function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content=None, tool_calls=[tc]))])


def _final_msg():
    return SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content=FINAL_TEXT, tool_calls=None))])


def _fake_client(responses):
    queue = list(responses)
    return SimpleNamespace(chat=SimpleNamespace(
        completions=SimpleNamespace(create=lambda **kw: queue.pop(0))))


def _run_with_bad_tool_args(tool_name, arguments):
    orch = MultiRoleOrchestrator(
        client=_fake_client([_tool_call_msg(tool_name, arguments), _final_msg()]),
        verbose=False, start_role="research")
    final = orch.run("查一下新能源汽车销量")
    tool_results = [m["content"] for m in orch.history if m["role"] == "tool"]
    return final, tool_results


def test_wrong_arg_name_returns_error_string_not_crash():
    final, tool_results = _run_with_bad_tool_args(
        "web_search", json.dumps({"q": "新能源汽车销量"}))
    assert final == FINAL_TEXT
    assert any("调用失败" in r for r in tool_results)


def test_missing_required_arg_returns_error_string_not_crash():
    final, tool_results = _run_with_bad_tool_args("web_search", "{}")
    assert final == FINAL_TEXT
    assert any("调用失败" in r for r in tool_results)


def test_non_numeric_stats_input_returns_error_string_not_crash():
    final, tool_results = _run_with_bad_tool_args(
        "descriptive_stats", json.dumps({"numbers": ["a", "b"]}))
    assert final == FINAL_TEXT
    assert any("调用失败" in r for r in tool_results)


def test_valid_tool_call_still_works(monkeypatch):
    # Unit tests do not spend a real Tavily request; the live acceptance run
    # separately proves that web_search returns attributable external results.
    monkeypatch.setitem(
        sys.modules["orchestrator"].TOOL_IMPLEMENTATIONS,
        "web_search",
        lambda query: json.dumps({
            "provider": "tavily",
            "query": query,
            "results": [{"url": "https://example.test", "content": "检索结果"}],
        }, ensure_ascii=False),
    )
    final, tool_results = _run_with_bad_tool_args(
        "web_search", json.dumps({"query": "新能源汽车 销量"}))
    assert final == FINAL_TEXT
    assert any("检索结果" in r for r in tool_results)
