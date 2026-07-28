"""Malformed apply_edits JSON must not abort customize with JSONDecodeError."""
import types

import agent


def _fake_client(arguments):
    fn = types.SimpleNamespace(name="apply_edits", arguments=arguments)
    tc = types.SimpleNamespace(id="c1", type="function", function=fn)
    msg = types.SimpleNamespace(tool_calls=[tc], content=None)
    resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])
    completions = types.SimpleNamespace(create=lambda **kw: resp)
    return types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))


def test_malformed_json_degrades_to_empty_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.jsx").write_text("// app", encoding="utf-8")
    (tmp_path / "src" / "theme.css").write_text("/* css */", encoding="utf-8")
    args = agent.customize(
        _fake_client('{"files": [{"path": "src/theme.css",}],'),  # trailing junk
        "model",
        tmp_path,
        "把按钮改成蓝色",
    )
    assert args["files"] == []


def test_valid_json_still_returns_files(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.jsx").write_text("// app", encoding="utf-8")
    (tmp_path / "src" / "theme.css").write_text("/* css */", encoding="utf-8")
    files = [{"path": "src/theme.css", "content": "body { color: red; }"}]
    import json
    args = agent.customize(
        _fake_client(json.dumps({"summary": "s", "files": files})),
        "model",
        tmp_path,
        "把文字改成红色",
    )
    assert args["files"] == files
