"""Empty problems JSON must not ZeroDivisionError in the accuracy summary."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import demo as cfm


class _Resp:
    def __init__(self):
        self.choices = [
            SimpleNamespace(
                message=SimpleNamespace(content="FINAL ANSWER: 1", tool_calls=None)
            )
        ]


class _Completions:
    @staticmethod
    def create(**kwargs):
        return _Resp()


class _Chat:
    completions = _Completions()


class _Client:
    chat = _Chat()


def test_empty_problems_summary_no_zerodiv(tmp_path, monkeypatch, capsys):
    path = tmp_path / "empty.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(cfm, "build_client_and_model", lambda model_override=None: (_Client(), "fake"))
    rc = cfm.main(["--problems", str(path), "--mode", "cot"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "0/0" in out
    assert "N/A" in out


def test_nonempty_summary_still_shows_percent(tmp_path, monkeypatch, capsys):
    path = tmp_path / "one.json"
    path.write_text(
        json.dumps([{"id": "1", "topic": "t", "question": "1+1?", "answer": 1}]),
        encoding="utf-8",
    )
    monkeypatch.setattr(cfm, "build_client_and_model", lambda model_override=None: (_Client(), "fake"))
    rc = cfm.main(["--problems", str(path), "--mode", "cot"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "1/1" in out
    assert "%" in out
