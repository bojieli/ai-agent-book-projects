"""apply_edits files 列表含 null/非 dict 项时，customize 应丢弃而非崩溃。"""
import json
import types

import pytest

import agent


def _fake_client(arguments):
    fn = types.SimpleNamespace(name="apply_edits", arguments=arguments)
    tc = types.SimpleNamespace(id="c1", type="function", function=fn)
    msg = types.SimpleNamespace(tool_calls=[tc], content=None)
    resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])
    completions = types.SimpleNamespace(create=lambda **kw: resp)
    return types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))


@pytest.fixture
def frontend_dir(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.jsx").write_text("// app", encoding="utf-8")
    (tmp_path / "src" / "theme.css").write_text("/* css */", encoding="utf-8")
    return tmp_path


def test_non_dict_file_items_dropped(frontend_dir):
    kept = {"path": "src/theme.css", "content": "body { color: blue; }"}
    args = agent.customize(
        _fake_client(json.dumps({
            "summary": "s",
            "files": [None, kept, "x", 1],
        })),
        "model", frontend_dir, "把按钮改成蓝色")
    assert args["files"] == [kept]


def test_normal_edits_unchanged(frontend_dir):
    files = [{"path": "src/theme.css", "content": "body { color: red; }"}]
    args = agent.customize(
        _fake_client(json.dumps({"summary": "s", "files": files})),
        "model", frontend_dir, "把文字改成红色")
    assert args["files"] == files
