"""web_search 对模型给出的异常 num_results（null / 非数字字符串）应兜底为默认值，
而不是抛 TypeError/ValueError 中断整个 Agent 循环。"""
import json

import base_tools


def _search_without_network(monkeypatch, num_results):
    """屏蔽真实网络与退避 sleep，只验证参数处理不崩溃。"""
    def _fake_post(*a, **k):
        raise RuntimeError("network disabled in test")

    monkeypatch.setattr(base_tools.requests, "post", _fake_post)
    monkeypatch.setattr(base_tools.time, "sleep", lambda *_a, **_k: None)
    return base_tools.web_search("python stock library", num_results)


def test_num_results_null_falls_back(monkeypatch):
    # 模型显式传 JSON null：.get(..., 6) 的默认值挡不住，应兜底为 6
    args = json.loads('{"query": "python stock library", "num_results": null}')
    result = _search_without_network(monkeypatch, args.get("num_results", 6))
    assert result["success"] is False  # 网络被禁用 -> 走失败返回，而不是异常
    assert "search failed" in result["error"]


def test_num_results_garbage_string_falls_back(monkeypatch):
    args = json.loads('{"query": "python stock library", "num_results": "five"}')
    result = _search_without_network(monkeypatch, args.get("num_results", 6))
    assert result["success"] is False
    assert "search failed" in result["error"]


def test_num_results_normal_still_clamped(monkeypatch):
    result = _search_without_network(monkeypatch, 3)
    assert result["success"] is False
    assert "search failed" in result["error"]
