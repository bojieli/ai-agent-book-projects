"""evidence manifest 模式校验（离线，不发真实请求）。"""

import copy

import pytest

from evidence import build_manifest, validate_manifest


def _minimal_run(route: str = "workflow", error=None) -> dict:
    call = {
        "call_id": "abc123",
        "provider": "moonshot",
        "model": "kimi-k3",
        "endpoint": "https://api.moonshot.cn/v1/chat/completions",
        "started_at": "2026-08-21T00:00:00+00:00",
        "finished_at": "2026-08-21T00:00:01+00:00",
        "latency_ms": 900.0,
        "status": "ok",
        "request": {"messages": []},
        "response_id": "chatcmpl-x",
        "usage": {"total_tokens": 100},
        "error": None,
    }
    return {
        "requirement_id": "programmer-overtime",
        "route": route,
        "input": "帮我画一个周末加班的程序员，风格丧一点",
        "rewrite": None,
        "nodes": [{"node": "rewrite", "call": call, "output": {}}],
        "image": None
        if error
        else {
            "path": "outputs/x/images/a.png",
            "sha256": "a" * 64,
            "bytes": 1234,
            "mime": "image/png",
        },
        "error": error,
    }


def _manifest(**overrides) -> dict:
    m = build_manifest(
        requirements=[{"id": "programmer-overtime", "text": "..."}],
        runs=[_minimal_run("workflow"), _minimal_run("native")],
        project_root=__import__("pathlib").Path("."),
        notes=["test"],
    )
    m.update(overrides)
    return m


def test_valid_manifest_passes():
    assert validate_manifest(_manifest()) == []


def test_missing_top_level_key():
    m = _manifest()
    del m["runs"]
    problems = validate_manifest(m)
    assert any("runs" in p for p in problems)


def test_credential_must_not_be_recorded():
    m = _manifest(credential_value_recorded=True)
    assert validate_manifest(m)


def test_unknown_requirement_id():
    m = _manifest()
    m["runs"][0]["requirement_id"] = "no-such-id"
    assert validate_manifest(m)


def test_bad_route_value():
    m = _manifest()
    m["runs"][0]["route"] = "hybrid"
    assert validate_manifest(m)


def test_success_run_requires_image_with_sha256():
    m = _manifest()
    m["runs"][0]["image"] = {"path": "x.png"}  # 缺 sha256/bytes/mime
    problems = validate_manifest(m)
    assert any("sha256" in p for p in problems)

    m2 = _manifest()
    m2["runs"][0]["image"]["sha256"] = "tooshort"
    assert any("sha256" in p for p in validate_manifest(m2))


def test_failed_run_without_image_is_accepted():
    m = _manifest()
    m["runs"][1] = _minimal_run("native", error="RuntimeError: quota")
    assert validate_manifest(m) == []


def test_node_without_call_record_fails():
    m = _manifest()
    m["runs"][0]["nodes"] = [{"node": "rewrite"}]
    assert validate_manifest(m)


def test_multi_call_node_shape():
    run = _minimal_run("workflow")
    call = run["nodes"][0]["call"]
    run["nodes"] = [
        {"node": "rewrite", "call": call, "output": {}},
        {"node": "image_generate", "calls": [copy.deepcopy(call), copy.deepcopy(call)]},
    ]
    m = _manifest(runs=[run])
    assert validate_manifest(m) == []
