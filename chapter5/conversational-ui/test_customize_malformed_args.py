"""模型返回的 apply_edits 参数缺字段/为 null 时，customize 应干净处理而非崩溃。"""
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


def test_files_null_normalized_to_empty(frontend_dir):
    """files 为显式 null → 归一化为空列表，下游迭代不崩溃。"""
    args = agent.customize(
        _fake_client(json.dumps({"summary": "s", "files": None})),
        "model", frontend_dir, "把按钮改成蓝色")
    assert args["files"] == []


def test_file_entry_missing_path_rejected_cleanly(frontend_dir):
    """文件项缺 path → 清晰的白名单拒绝（RuntimeError），而非 KeyError。"""
    with pytest.raises(RuntimeError, match="白名单"):
        agent.customize(
            _fake_client(json.dumps({"summary": "s", "files": [{"content": "x"}]})),
            "model", frontend_dir, "把按钮改成蓝色")


def test_normal_edits_pass(frontend_dir):
    """合法参数不受影响。"""
    files = [{"path": "src/theme.css", "content": "body { color: red; }"}]
    args = agent.customize(
        _fake_client(json.dumps({"summary": "s", "files": files})),
        "model", frontend_dir, "把文字改成红色")
    assert args["files"] == files


def test_file_entry_missing_content_dropped(frontend_dir):
    """文件项有合法 path 但缺 content → 丢弃该项，避免下游写盘 f["content"]
    抛出 KeyError 而中断整个 demo（与缺 path 抛白名单错误对称处理）。"""
    args = agent.customize(
        _fake_client(json.dumps({"summary": "s", "files": [{"path": "src/theme.css"}]})),
        "model", frontend_dir, "把按钮改成蓝色")
    assert args["files"] == []
