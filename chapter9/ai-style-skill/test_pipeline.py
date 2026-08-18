"""开放式规则提炼与 LLM-as-a-judge 流程的离线单元测试。"""

from __future__ import annotations

import json

import extract_rules
from evaluate import evaluate_rules
from judge import calibrate, score_text
from llm_client import default_model
from skill_manager import merge_rules, prune_rules, render_skill_md, write_skill


def _rule(rule_id="rule-worth-noting", sources=None):
    return {
        "id": rule_id,
        "name": "避免重复强调套话",
        "definition": "连续用空泛的强调短语引出普通信息时命中；一次必要的风险提示不命中。",
        "detector": {"type": "llm"},
        "bad_example": "值得注意的是，甲。值得注意的是，乙。",
        "good_example": "甲，乙。",
        "rewrite_hint": "删除重复引导语，直接陈述信息。",
        "scope": ["邮件"],
        "source_ids": sources or ["fp-022"],
        "status": "candidate",
    }


def test_extract_accepts_open_ended_rule_and_forces_llm_judge(monkeypatch):
    pairs = [{
        "id": "fp-022",
        "scene": "邮件",
        "before": "值得注意的是，甲。值得注意的是，乙。",
        "after": "甲，乙。",
        "correction": "别重复强调",
    }]
    payload = {
        "rules": [{
            "id": "rule-worth-noting",
            "name": "避免重复强调套话",
            "definition": "重复强调普通信息时命中。",
            "detector": {"type": "regex", "pattern": "值得注意的是"},
            "bad_example": pairs[0]["before"],
            "good_example": pairs[0]["after"],
            "rewrite_hint": "直接说结论。",
            "scope": ["邮件"],
            "source_ids": ["fp-022"],
        }]
    }

    def fake_chat(messages, **kwargs):
        assert "不要依赖任何预置的模式清单" in messages[0]["content"]
        return json.dumps(payload, ensure_ascii=False), {"response": {"id": "resp_test"}}

    monkeypatch.setattr(extract_rules, "chat", fake_chat)
    candidates, receipt = extract_rules.extract_with_llm(
        pairs, provider="openai", model="gpt-5.6-sol"
    )
    assert receipt["response"]["id"] == "resp_test"
    assert [candidate["id"] for candidate in candidates] == ["rule-worth-noting"]
    assert candidates[0]["detector"] == {"type": "llm"}


def test_extract_rejects_hallucinated_sources_and_examples(monkeypatch):
    pairs = [{
        "id": "fp-001", "scene": "邮件", "before": "原文", "after": "改文", "correction": "修改"
    }]
    payload = {"rules": [
        {
            "id": "rule-invented", "name": "n", "definition": "d",
            "bad_example": "编造坏例", "good_example": "编造好例",
            "rewrite_hint": "h", "scope": [], "source_ids": ["fp-999"],
        }
    ]}
    monkeypatch.setattr(
        extract_rules, "chat", lambda *args, **kwargs: (json.dumps(payload), {})
    )
    candidates, _ = extract_rules.extract_with_llm(pairs, provider="openai")
    assert candidates == []


def test_merge_uses_stable_rule_id_not_detector_type():
    first = _rule("rule-worth-noting", ["fp-022"])
    repeated = _rule("rule-worth-noting", ["fp-025"])
    novel = _rule("rule-passive-stacking", ["fp-023"])
    novel["name"] = "避免连续被动句"

    rules, report = merge_rules([], [first])
    rules, report = merge_rules(rules, [repeated, novel])
    assert len(rules) == 2
    assert report["merged"] == ["rule-worth-noting"]
    assert report["added"] == ["rule-passive-stacking"]
    merged = next(rule for rule in rules if rule["id"] == "rule-worth-noting")
    assert set(merged["source_ids"]) == {"fp-022", "fp-025"}


def test_prune_archives_idle_and_contradicted():
    rules = [
        {"id": "rule-a", "definition": "a", "source_ids": ["fp-001"], "last_confirmed_batch": 1},
        {"id": "rule-b", "definition": "b", "source_ids": ["fp-002"], "last_confirmed_batch": 3},
        {"id": "rule-c", "definition": "c", "source_ids": ["fp-003"], "last_confirmed_batch": 3},
    ]
    active, archived = prune_rules(
        rules, current_batch=4, idle_batches=2, contradicted_ids={"rule-c"}
    )
    assert [rule["id"] for rule in active] == ["rule-b"]
    assert {rule["id"] for rule in archived} == {"rule-a", "rule-c"}


def test_calibration_uses_external_labels_linked_by_feedback_source():
    rule = _rule(sources=["fp-022", "fp-025"])
    golden = [
        {
            "id": "g1", "text": "坏：重复强调",
            "labels": [{"source_ids": ["fp-022", "fp-025"], "expected": True}],
        },
        {
            "id": "g2", "text": "好：单次必要提示",
            "labels": [{"source_ids": ["fp-022", "fp-025"], "expected": False}],
        },
    ]

    def good_judge(rules, texts):
        return {
            (item_rule["id"], text["id"]): {
                "hit": text["text"].startswith("坏"), "evidence": "重复强调"
            }
            for item_rule in rules for text in texts
        }

    result = calibrate(rule, golden, good_judge)
    assert result["total"] == 2
    assert result["agreement"] == 1.0
    assert result["decision"] == "activate"


def test_calibration_rejects_missing_gold_or_bad_judge():
    rule = _rule()
    no_coverage = calibrate(rule, [], lambda rules, texts: {})
    assert no_coverage["decision"] == "reject"

    golden = [{
        "id": "g1", "text": "应命中",
        "labels": [{"source_ids": ["fp-022"], "expected": True}],
    }]
    bad = calibrate(
        rule,
        golden,
        lambda rules, texts: {(rule["id"], "g1"): {"hit": False, "evidence": ""}},
    )
    assert bad["decision"] == "reject"


def test_score_text_batches_all_rules_in_one_judge_call():
    rules = [_rule("rule-a", ["fp-a"]), _rule("rule-b", ["fp-b"])]
    calls = []

    def judge(batch_rules, texts):
        calls.append((batch_rules, texts))
        return {
            ("rule-a", "sample"): {"hit": True, "evidence": "证据"},
            ("rule-b", "sample"): {"hit": False, "evidence": ""},
        }

    fired = score_text("待评文本", rules, judge, text_id="sample")
    assert list(fired) == ["rule-a"]
    assert fired["rule-a"]["evidence"] == "证据"
    assert len(calls) == 1 and len(calls[0][0]) == 2


def test_evaluation_maps_human_source_labels_to_dynamic_rule_ids():
    rules = [_rule("rule-dynamic-name", ["fp-new"])]
    eval_texts = {
        "boundary": [{"id": "b1", "text": "坏文本", "expected_sources": ["fp-new"]}],
        "retention": [{"id": "r1", "text": "好文本"}],
    }

    def judge(batch_rules, texts):
        text = texts[0]
        return {
            (batch_rules[0]["id"], text["id"]): {
                "hit": text["id"] == "b1", "evidence": "坏文本" if text["id"] == "b1" else ""
            }
        }

    metrics = evaluate_rules(rules, eval_texts, judge)
    assert metrics["boundary_detection_rate"] == 1.0
    assert metrics["retention_harm_rate"] == 0.0


def test_skill_md_describes_llm_judge_and_structure(tmp_path):
    rules = [_rule()]
    markdown = render_skill_md(rules)
    assert "LLM judge 语义判定" in markdown
    assert "预置" not in markdown
    for section in ("**定义**", "**坏例**", "**好例**", "**作用域**", "**检测方法**"):
        assert section in markdown
    path = write_skill(rules, tmp_path)
    assert path.exists()
    assert json.loads((tmp_path / "rules.json").read_text(encoding="utf-8"))[0]["id"]


def test_openai_default_is_gpt_5_6_sol():
    assert default_model("openai") == "gpt-5.6-sol"
