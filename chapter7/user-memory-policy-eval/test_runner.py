from __future__ import annotations

import json
from pathlib import Path

from runner import HERE, memory_text, parse_json, score, sha256


def case_fixture() -> dict:
    return json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))["cases"][1]


def test_all_memory_encodings_retain_scope_fields() -> None:
    memory = case_fixture()["memory"]
    for fmt in ("json", "markdown", "python"):
        rendered = memory_text(memory, fmt)
        assert memory["id"] in rendered
        assert memory["scope"] in rendered
        assert "学术论文" in rendered


def test_parse_json_extracts_embedded_object() -> None:
    assert parse_json("Here is the result: {\"decision\": \"ignore\"}")["decision"] == "ignore"


def test_prefix_scorer_rejects_applying_scoped_paper_memory_to_x() -> None:
    case = case_fixture()
    good = {
        "decision": "override",
        "memory_ids_used": [],
        "next_step_type": "answer",
        "next_step": "用 X 的短帖风格回答当前请求",
        "rationale": "当前媒介是 X，不适用学术论文记忆",
    }
    bad = {
        "decision": "apply",
        "memory_ids_used": [case["memory"]["id"]],
        "next_step_type": "apply_memory",
        "next_step": "按照学术论文风格回答",
        "rationale": "沿用历史偏好",
    }
    assert score(case, good)["passed"] is True
    assert score(case, bad)["passed"] is False


def test_saved_campaign_manifest_binds_report_cases_and_runner() -> None:
    manifest_path = HERE / "results" / "manifest.json"
    report_path = HERE / "results" / "policy_prefix_live.json"
    if not manifest_path.exists() or not report_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert manifest["experiment"] == report["experiment"] == "6-5"
    assert manifest["report"] == "results/policy_prefix_live.json"
    assert manifest["report_sha256"] == sha256(report_path)
    assert manifest["case_sha256"] == sha256(HERE / "cases.json")
    assert manifest["runner"] == "runner.py"
    assert manifest["runner_sha256"] == sha256(HERE / "runner.py")
    assert manifest["records"] == len(report["records"]) == 33
