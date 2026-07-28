"""Proofreading must return a dict when the model emits a JSON array or junk."""
from agents import _loads_lenient, _report_issues, proofreading_agent


def test_loads_lenient_empty_and_junk_return_none():
    assert _loads_lenient("") is None
    assert _loads_lenient("not json") is None
    assert _loads_lenient('{"a": 1}') == {"a": 1}


def test_report_issues_non_dict():
    assert _report_issues([]) == []
    assert _report_issues(None) == []


def test_proofreading_agent_json_array_returns_empty_dict(monkeypatch):
    calls = []

    def fake_llm_chat(client, tracker, agent, messages, json_mode=False, note=""):
        calls.append(note)
        return "[]"

    monkeypatch.setattr("agents.llm_chat", fake_llm_chat)
    report = proofreading_agent(
        client=object(),
        tracker=type("T", (), {"record": lambda *a, **k: None})(),
        translations={"ch1": "hello"},
        glossary=[],
    )
    assert report == {}
    assert _report_issues(report) == []
    assert report.get("chapters_need_revision", []) == []
    assert calls == ["一致性审校"]


def test_proofreading_agent_valid_object(monkeypatch):
    payload = {
        "issues": [{"chapter": "ch1", "detail": "x"}],
        "chapters_need_revision": ["ch1"],
        "summary": "ok",
    }

    def fake_llm_chat(client, tracker, agent, messages, json_mode=False, note=""):
        import json
        return json.dumps(payload)

    monkeypatch.setattr("agents.llm_chat", fake_llm_chat)
    report = proofreading_agent(
        client=object(),
        tracker=type("T", (), {"record": lambda *a, **k: None})(),
        translations={"ch1": "hello"},
        glossary=[],
    )
    assert report == payload
